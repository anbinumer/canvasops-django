"""
Canvas Vimeo Content Scanner

A tool that scans a Canvas course for Vimeo content and captures both URLs and iframe embeddings.
- Scans: syllabus, pages, assignments, quizzes, discussions, announcements, and modules
- Detects both direct Vimeo links and embedded iframes
- Creates an Excel report of all findings with complete embedding code
"""

import requests
from typing import Optional, Dict, List, Tuple
import logging
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import pytz
import re
import concurrent.futures

class CanvasVimeoScanner:
    def __init__(self, base_url: str, api_token: str):
        """
        Initialize the Canvas Vimeo Scanner.
        
        Args:
            base_url (str): The base URL of your Canvas instance
            api_token (str): Your Canvas API token
        """
        self.base_url = f"https://{base_url}".rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize list to store findings
        self.findings_list = []

        # Vimeo URL patterns
        self.vimeo_patterns = [
            r'https?://(?:www\.)?vimeo\.com/\d+',
            r'https?://player\.vimeo\.com/video/\d+',
        ]

    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Make a paginated GET request to the Canvas API."""
        if params is None:
            params = {}
        
        params['per_page'] = 100
        url = f"{self.api_url}/{endpoint}"
        
        try:
            results = []
            while url:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                if isinstance(data, list):
                    results.extend(data)
                else:
                    return data
                
                url = response.links.get('next', {}).get('url')
                params = {}
            
            return results
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def find_vimeo_content(self, html_content: str, location_type: str, location_url: str, 
                          course_id: str, course_name: str, item_name: str = "") -> None:
        """
        Find Vimeo content in HTML and store findings.
        """
        if not html_content:
            return

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all iframes
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if any(re.search(pattern, src) for pattern in self.vimeo_patterns):
                    self.findings_list.append({
                        'Course ID': course_id,
                        'Course Name': course_name,
                        'Item Name': item_name,
                        'Location Type': location_type,
                        'Location URL': location_url,
                        'Content Type': 'Embedded iframe',
                        'Vimeo URL': src,
                        'Embedding Code': str(iframe),
                        'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                    })
            
            # Find all links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if any(re.search(pattern, href) for pattern in self.vimeo_patterns):
                    self.findings_list.append({
                        'Course ID': course_id,
                        'Course Name': course_name,
                        'Item Name': item_name,
                        'Location Type': location_type,
                        'Location URL': location_url,
                        'Content Type': 'Direct link',
                        'Vimeo URL': href,
                        'Embedding Code': '',  # Empty for direct links
                        'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                    })

        except Exception as e:
            self.logger.error(f"Error processing content: {str(e)}")

    def scan_course(self, course_id: str) -> None:
        """
        Scan a course for Vimeo content.
        """
        self.logger.info(f"Starting scan for course {course_id}")
        
        # Get course information
        course_info = self.make_request(f"courses/{course_id}")
        course_name = course_info.get('name', 'Unknown')
        
        try:
            # Process syllabus
            syllabus = self.make_request(f"courses/{course_id}", {'include[]': 'syllabus_body'})
            if 'syllabus_body' in syllabus and syllabus['syllabus_body']:
                self.find_vimeo_content(
                    syllabus['syllabus_body'],
                    'Syllabus',
                    f"{self.base_url}/courses/{course_id}/assignments/syllabus",
                    course_id,
                    course_name,
                    "Syllabus"
                )
            
            # Process pages
            pages = self.make_request(f"courses/{course_id}/pages")
            for page in pages:
                page_url = page['url']
                page_data = self.make_request(f"courses/{course_id}/pages/{page_url}")
                if 'body' in page_data:
                    self.find_vimeo_content(
                        page_data['body'],
                        'Page',
                        page['html_url'],
                        course_id,
                        course_name,
                        page['title']
                    )

            # Process assignments
            assignments = self.make_request(f"courses/{course_id}/assignments")
            for assignment in assignments:
                if 'description' in assignment and assignment['description']:
                    self.find_vimeo_content(
                        assignment['description'],
                        'Assignment',
                        assignment['html_url'],
                        course_id,
                        course_name,
                        assignment['name']
                    )

            # Process quizzes
            quizzes = self.make_request(f"courses/{course_id}/quizzes")
            for quiz in quizzes:
                if 'description' in quiz and quiz['description']:
                    self.find_vimeo_content(
                        quiz['description'],
                        'Quiz',
                        quiz['html_url'],
                        course_id,
                        course_name,
                        quiz['title']
                    )
                
                # Process quiz questions
                questions = self.make_request(f"courses/{course_id}/quizzes/{quiz['id']}/questions")
                for question in questions:
                    if 'question_text' in question and question['question_text']:
                        self.find_vimeo_content(
                            question['question_text'],
                            'Quiz Question',
                            f"{quiz['html_url']}/questions/{question['id']}",
                            course_id,
                            course_name,
                            f"{quiz['title']} - Question {question['id']}"
                        )

            # Process discussions
            discussions = self.make_request(f"courses/{course_id}/discussion_topics")
            for discussion in discussions:
                if 'message' in discussion and discussion['message']:
                    self.find_vimeo_content(
                        discussion['message'],
                        'Discussion',
                        discussion['html_url'],
                        course_id,
                        course_name,
                        discussion['title']
                    )

            # Process announcements
            announcements = self.make_request(f"courses/{course_id}/discussion_topics?only_announcements=true")
            for announcement in announcements:
                if 'message' in announcement and announcement['message']:
                    self.find_vimeo_content(
                        announcement['message'],
                        'Announcement',
                        announcement['html_url'],
                        course_id,
                        course_name,
                        announcement['title']
                    )

            self.logger.info(f"Completed scanning course {course_id}")
            
        except Exception as e:
            self.logger.error(f"Error scanning course {course_id}: {str(e)}")
            raise

    def generate_excel_report(self, output_file: str = 'canvas_vimeo_content_report.xlsx') -> None:
        """
        Generate an Excel report from the findings.
        """
        if not self.findings_list:
            self.logger.warning("No Vimeo content found to report")
            return
        
        df = pd.DataFrame(self.findings_list)
        
        # Reorder columns for better readability
        columns_order = [
            'Course ID',
            'Course Name',
            'Item Name',
            'Location Type',
            'Location URL',
            'Content Type',
            'Vimeo URL',
            'Embedding Code',
            'Timestamp'
        ]
        df = df[columns_order]
        
        try:
            df.to_excel(output_file, index=False, sheet_name='Vimeo Content')
            self.logger.info(f"Report generated successfully: {output_file}")
        except Exception as e:
            self.logger.error(f"Error generating Excel report: {str(e)}")
            raise

def main():
    # Initialize scanner with your credentials
    scanner = CanvasVimeoScanner(
        base_url="aculeo.beta.instructure.com",
        api_token="22643~eBYKrWCy2cFYUAnCrKLBEkmrvRNeaErTC7QGeJPu3G7GJ9He3DU6mru6wFvczJyn"
    )
    
    try:
        subaccount_id = input("Please enter the subaccount ID: ")
        
        # Get courses in the subaccount
        courses = scanner.make_request(f"accounts/{subaccount_id}/courses")
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(scanner.scan_course, course['id']): course for course in courses}
            for future in concurrent.futures.as_completed(futures):
                course = futures[future]
                try:
                    future.result()
                    print(f"Successfully scanned course: {course['name']} (ID: {course['id']})")
                except Exception as e:
                    print(f"Error scanning course {course['name']} (ID: {course['id']}): {str(e)}")
        
        # Generate Excel report
        scanner.generate_excel_report()
        
    except Exception as e:
        print(f"\nError during processing: {str(e)}")

if __name__ == "__main__":
    main()