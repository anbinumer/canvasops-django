"""
Canvas URL Scanner and Replacer

A tool that scans a Canvas course for specific URLs and replaces them with new ones.
- Scans: syllabus, pages, assignments, quizzes, discussions, announcements, and modules
- Replaces target URLs with their specified replacements
- Creates an Excel report of all changes made

Usage: Update the url_mappings in main() with your target and replacement URLs.
"""

import requests
from typing import Optional, Dict, List, Tuple
import logging
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import pytz
import json
import re

class CanvasURLScanner:
    def __init__(self, base_url: str, api_token: str, url_mappings: Dict[str, str]):
        """
        Initialize the Canvas URL Scanner for scanning and replacing URLs.
        
        Args:
            base_url (str): The base URL of your Canvas instance
            api_token (str): Your Canvas API token
            url_mappings (dict): Dictionary of target URLs and their replacements
                               e.g., {"old_url1": "new_url1", "old_url2": "new_url2"}
        """
        self.base_url = f"https://{base_url}".rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.url_mappings = url_mappings
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize list to store findings for report
        self.findings_list = []

        # Log URL mappings
        self.logger.info("Initialized with the following URL mappings:")
        for old_url, new_url in self.url_mappings.items():
            self.logger.info(f"  {old_url} → {new_url}")

    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Make a paginated GET request to the Canvas API.
        """
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

    def get_syllabus(self, course_id: str) -> Tuple[bool, str, str]:
        """
        Fetch syllabus content for a given course.
        """
        url = f"{self.api_url}/courses/{course_id}"
        params = {'include[]': 'syllabus_body'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            self.logger.info(f"Fetching syllabus from course {course_id}")
            
            response.raise_for_status()
            data = response.json()
            
            if 'syllabus_body' in data:
                self.logger.info("Found syllabus_body in response")
                if data['syllabus_body']:
                    self.logger.info(f"Syllabus content length: {len(data['syllabus_body'])}")
                    for target_url in self.url_mappings.keys():
                        if target_url in data['syllabus_body']:
                            self.logger.info(f"Target URL found in syllabus content: {target_url}")
                            start_idx = data['syllabus_body'].find(target_url)
                            context = data['syllabus_body'][max(0, start_idx-50):min(len(data['syllabus_body']), start_idx+150)]
                            self.logger.info(f"URL context: {context}")
                    return True, data['syllabus_body'], ""
                else:
                    self.logger.info("Syllabus body is empty")
            else:
                self.logger.info("No syllabus_body found in response")
            return False, "", "Syllabus content empty or not found"
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching syllabus: {str(e)}")
            return False, "", f"Error fetching syllabus: {str(e)}"

    def update_content(self, course_id: str, content_type: str, content_id: str, new_content: str) -> Tuple[bool, str]:
        """
        Update content in Canvas for various content types.
        """
        try:
            if content_type == 'syllabus':
                url = f"{self.api_url}/courses/{course_id}"
                payload = {
                    'course': {
                        'syllabus_body': new_content
                    }
                }
            elif content_type == 'page':
                url = f"{self.api_url}/courses/{course_id}/pages/{content_id}"
                payload = {
                    'wiki_page': {
                        'body': new_content
                    }
                }
            elif content_type == 'assignment':
                url = f"{self.api_url}/courses/{course_id}/assignments/{content_id}"
                payload = {
                    'assignment': {
                        'description': new_content
                    }
                }
            elif content_type == 'quiz':
                url = f"{self.api_url}/courses/{course_id}/quizzes/{content_id}"
                payload = {
                    'quiz': {
                        'description': new_content
                    }
                }
            elif content_type == 'quiz_question':
                quiz_id, question_id = content_id.split('/')
                url = f"{self.api_url}/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}"
                payload = {
                    'question': {
                        'question_text': new_content
                    }
                }
            elif content_type == 'discussion':
                url = f"{self.api_url}/courses/{course_id}/discussion_topics/{content_id}"
                payload = {
                    'message': new_content
                }
            elif content_type == 'announcement':
                url = f"{self.api_url}/courses/{course_id}/discussion_topics/{content_id}"
                payload = {
                    'message': new_content
                }
            
            self.logger.info(f"Updating {content_type} at URL: {url}")
            
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Successfully updated {content_type}")
            return True, ""
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error updating {content_type}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def replace_urls_in_content(self, content: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Replace multiple target URLs with their replacements in content using BeautifulSoup.
        """
        if not content:
            self.logger.info("Content is empty, skipping replacement")
            return content, []

        replacements = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find and replace URLs in href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                for target_url, replacement_url in self.url_mappings.items():
                    if target_url in href:
                        self.logger.info(f"Found target URL in href: {href}")
                        new_href = href.replace(target_url, replacement_url)
                        link['href'] = new_href
                        replacements.append((target_url, replacement_url))
            
            # Find and replace URLs in data-api-endpoint attributes
            for element in soup.find_all(attrs={"data-api-endpoint": True}):
                endpoint = element['data-api-endpoint']
                for target_url, replacement_url in self.url_mappings.items():
                    if target_url in endpoint:
                        self.logger.info(f"Found target URL in data-api-endpoint: {endpoint}")
                        new_endpoint = endpoint.replace(target_url, replacement_url)
                        element['data-api-endpoint'] = new_endpoint
                        replacements.append((target_url, replacement_url))
            
            # Also check for URLs in plain text nodes
            text_nodes = soup.find_all(string=True)
            for text_node in text_nodes:
                if text_node.parent.name not in ['script', 'style']:
                    for target_url, replacement_url in self.url_mappings.items():
                        if target_url in text_node:
                            self.logger.info(f"Found target URL in text: {text_node}")
                            new_text = text_node.replace(target_url, replacement_url)
                            text_node.replace_with(new_text)
                            replacements.append((target_url, replacement_url))

            new_content = str(soup)
            
            if replacements:
                self.logger.info(f"Made {len(replacements)} replacements in content")
            
            return new_content, replacements

        except Exception as e:
            self.logger.error(f"Error during URL replacement: {str(e)}")
            return content, []

    def scan_and_replace(self, course_id: str) -> None:
        """
        Scan a course for target URLs and replace with new URLs.
        """
        self.logger.info(f"Starting scan and replace for course {course_id}")
        
        # Get course information
        course_info = self.make_request(f"courses/{course_id}")
        course_name = course_info.get('name', 'Unknown')
        
        try:
            # Process syllabus
            self.logger.info("Processing syllabus...")
            success, syllabus_content, error = self.get_syllabus(course_id)
            
            if success and syllabus_content:
                self.logger.info("Retrieved syllabus content successfully")
                new_content, replacements = self.replace_urls_in_content(syllabus_content)
                if replacements:
                    self.logger.info(f"Found {len(replacements)} URLs to replace in syllabus")
                    success, error = self.update_content(course_id, 'syllabus', '', new_content)
                    for old_url, new_url in replacements:
                        self.findings_list.append({
                            'Course ID': course_id,
                            'Course Name': course_name,
                            'Location Type': 'Syllabus',
                            'Location URL': f"{self.base_url}/courses/{course_id}/assignments/syllabus",
                            'Original URL': old_url,
                            'New URL': new_url,
                            'Update Status': 'Success' if success else f'Failed: {error}',
                            'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                        })
                else:
                    self.logger.info("No URLs found in syllabus to replace")
            else:
                self.logger.warning(f"Failed to get syllabus content: {error}")
            
            # Process pages
            pages = self.make_request(f"courses/{course_id}/pages")
            self.logger.info(f"Found {len(pages)} pages to process")
            
            for page in pages:
                page_url = page['url']
                try:
                    page_data = self.make_request(f"courses/{course_id}/pages/{page_url}")
                    if 'body' in page_data:
                        new_content, replacements = self.replace_urls_in_content(page_data['body'])
                        if replacements:
                            success, error = self.update_content(course_id, 'page', page_url, new_content)
                            for old_url, new_url in replacements:
                                self.findings_list.append({
                                    'Course ID': course_id,
                                    'Course Name': course_name,
                                    'Location Type': 'Page',
                                    'Location URL': page['html_url'],
                                    'Original URL': old_url,
                                    'New URL': new_url,
                                    'Update Status': 'Success' if success else f'Failed: {error}',
                                    'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                })
                except Exception as e:
                    self.logger.warning(f"Error processing page {page_url}: {str(e)}")
                    continue

            # Process assignments
            self.logger.info("Processing assignments...")
            assignments = self.make_request(f"courses/{course_id}/assignments")
            self.logger.info(f"Found {len(assignments)} assignments to process")
            
            for assignment in assignments:
                try:
                    if 'description' in assignment and assignment['description']:
                        new_content, replacements = self.replace_urls_in_content(assignment['description'])
                        if replacements:
                            success, error = self.update_content(course_id, 'assignment', str(assignment['id']), new_content)
                            for old_url, new_url in replacements:
                                self.findings_list.append({
                                    'Course ID': course_id,
                                    'Course Name': course_name,
                                    'Location Type': 'Assignment',
                                    'Location URL': assignment['html_url'],
                                    'Original URL': old_url,
                                    'New URL': new_url,
                                    'Update Status': 'Success' if success else f'Failed: {error}',
                                    'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                })
                except Exception as e:
                    self.logger.warning(f"Error processing assignment {assignment.get('id')}: {str(e)}")
                    continue

            # Process quizzes
            self.logger.info("Processing quizzes...")
            quizzes = self.make_request(f"courses/{course_id}/quizzes")
            self.logger.info(f"Found {len(quizzes)} quizzes to process")
            
            for quiz in quizzes:
                try:
                    if 'description' in quiz and quiz['description']:
                        new_content, replacements = self.replace_urls_in_content(quiz['description'])
                        if replacements:
                            success, error = self.update_content(course_id, 'quiz', str(quiz['id']), new_content)
                            for old_url, new_url in replacements:
                                self.findings_list.append({
                                    'Course ID': course_id,
                                    'Course Name': course_name,
                                    'Location Type': 'Quiz',
                                    'Location URL': quiz['html_url'],
                                    'Original URL': old_url,
                                    'New URL': new_url,
                                    'Update Status': 'Success' if success else f'Failed: {error}',
                                    'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                })
                    
                    # Process quiz questions
                    questions = self.make_request(f"courses/{course_id}/quizzes/{quiz['id']}/questions")
                    for question in questions:
                        if 'question_text' in question and question['question_text']:
                            new_content, replacements = self.replace_urls_in_content(question['question_text'])
                            if replacements:
                                success, error = self.update_content(course_id, 'quiz_question', 
                                                                  f"{quiz['id']}/{question['id']}", new_content)
                                for old_url, new_url in replacements:
                                    self.findings_list.append({
                                        'Course ID': course_id,
                                        'Course Name': course_name,
                                        'Location Type': 'Quiz Question',
                                        'Location URL': f"{quiz['html_url']}/questions/{question['id']}",
                                        'Original URL': old_url,
                                        'New URL': new_url,
                                        'Update Status': 'Success' if success else f'Failed: {error}',
                                        'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                    })
                except Exception as e:
                    self.logger.warning(f"Error processing quiz {quiz.get('id')}: {str(e)}")
                    continue

            # Process discussions
            self.logger.info("Processing discussions...")
            discussions = self.make_request(f"courses/{course_id}/discussion_topics")
            self.logger.info(f"Found {len(discussions)} discussions to process")
            
            for discussion in discussions:
                try:
                    discussion_id = discussion.get('id')
                    title = discussion.get('title', 'No title')
                    self.logger.info(f"Processing discussion: {title} (ID: {discussion_id})")
                    
                    # Get full discussion content
                    discussion_detail = self.make_request(f"courses/{course_id}/discussion_topics/{discussion_id}")
                    
                    # Check main discussion message
                    if 'message' in discussion_detail and discussion_detail['message']:
                        new_content, replacements = self.replace_urls_in_content(discussion_detail['message'])
                        if replacements:
                            success, error = self.update_content(course_id, 'discussion', str(discussion_id), new_content)
                            for old_url, new_url in replacements:
                                self.findings_list.append({
                                    'Course ID': course_id,
                                    'Course Name': course_name,
                                    'Location Type': 'Discussion Message',
                                    'Location URL': discussion.get('html_url', ''),
                                    'Original URL': old_url,
                                    'New URL': new_url,
                                    'Update Status': 'Success' if success else f'Failed: {error}',
                                    'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                })
                    
                except Exception as e:
                    self.logger.error(f"Error processing discussion {discussion_id}: {str(e)}")
                    continue
            
            # Process announcements
            self.logger.info("Processing announcements...")
            announcements = self.make_request(f"courses/{course_id}/discussion_topics?only_announcements=true")
            self.logger.info(f"Found {len(announcements)} announcements to process")
            
            for announcement in announcements:
                try:
                    announcement_id = announcement.get('id')
                    title = announcement.get('title', 'No title')
                    self.logger.info(f"Processing announcement: {title} (ID: {announcement_id})")
                    
                    if 'message' in announcement and announcement['message']:
                        new_content, replacements = self.replace_urls_in_content(announcement['message'])
                        if replacements:
                            success, error = self.update_content(course_id, 'announcement', str(announcement_id), new_content)
                            for old_url, new_url in replacements:
                                self.findings_list.append({
                                    'Course ID': course_id,
                                    'Course Name': course_name,
                                    'Location Type': 'Announcement',
                                    'Location URL': announcement.get('html_url', ''),
                                    'Original URL': old_url,
                                    'New URL': new_url,
                                    'Update Status': 'Success' if success else f'Failed: {error}',
                                    'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                })
                
                except Exception as e:
                    self.logger.error(f"Error processing announcement {announcement_id}: {str(e)}")
                    continue

            # Process modules
            self.logger.info("Processing modules...")
            modules = self.make_request(f"courses/{course_id}/modules")
            self.logger.info(f"Found {len(modules)} modules to process")
            
            for module in modules:
                module_items = self.make_request(f"courses/{course_id}/modules/{module['id']}/items")
                for item in module_items:
                    if item['type'] == 'ExternalUrl':
                        if 'external_url' in item and item['external_url']:
                            new_content, replacements = self.replace_urls_in_content(item['external_url'])
                            if replacements:
                                self.findings_list.append({
                                    'Course ID': course_id,
                                    'Course Name': course_name,
                                    'Location Type': 'Module Item (External URL)',
                                    'Location URL': item['html_url'],
                                    'Original URL': item['external_url'],
                                    'New URL': new_content,  # Assuming the new content is the updated URL
                                    'Update Status': 'Processed',
                                    'Timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
                                })

            self.logger.info(f"Completed processing course {course_id}")
            self.logger.info(f"Total replacements: {len(self.findings_list)}")
            
        except Exception as e:
            self.logger.error(f"Error processing course {course_id}: {str(e)}")
            raise

    def generate_excel_report(self, output_file: str = 'canvas_url_replacement_report.xlsx') -> None:
        """
        Generate an Excel report from the findings.
        """
        if not self.findings_list:
            self.logger.warning("No replacements to report")
            return
        
        df = pd.DataFrame(self.findings_list)
        
        # Reorder columns for better readability
        columns_order = [
            'Course ID',
            'Course Name',
            'Location Type',
            'Location URL',
            'Original URL',
            'New URL',
            'Update Status',
            'Timestamp'
        ]
        df = df[columns_order]
        
        try:
            df.to_excel(output_file, index=False, sheet_name='URL Replacements')
            self.logger.info(f"Report generated successfully: {output_file}")
        except Exception as e:
            self.logger.error(f"Error generating Excel report: {str(e)}")
            raise

def main():
    # URL mappings - add as many as needed
    url_mappings = {
        "https://canvas.acu.edu.au/courses/28429": "https://canvas.acu.edu.au/courses/ABCD",
        # Add more mappings as needed, for example:
        # "https://canvas.acu.edu.au/courses/12345": "https://canvas.acu.edu.au/courses/67890",
    }

    # Initialize scanner with your credentials and URL mappings
    scanner = CanvasURLScanner(
        base_url="aculeo.beta.instructure.com",
        api_token="22643~YXYUtcRY8R7YPKm9x6Xt3RTYuwfz9MTz2YwPvHVvJ6wHwmwzaPaEe4U86P3zNCNN",
        url_mappings=url_mappings
    )
    
    try:
        course_id = "28042"  # Your specific course ID
        scanner.scan_and_replace(course_id)
        
        # Generate Excel report
        scanner.generate_excel_report()
        
    except Exception as e:
        print(f"\nError during processing: {str(e)}")

if __name__ == "__main__":
    main()