"""
Canvas Syllabus Scanner - Find Only Version

This script scans Canvas course syllabi for specific text but does not make any changes.
It's designed to identify all courses that contain variants of the "Adjust Events and Due Dates" instruction.
"""

import requests
from typing import Optional, Dict, List, Tuple, Union
import logging
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import pytz
import re
import concurrent.futures
import time

class CanvasSyllabusScanner:
    def __init__(self, base_url: str, api_token: str):
        """Initialize the Canvas Syllabus Scanner tool."""
        self.base_url = f"https://{base_url}".rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('syllabus_scan.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize list to store findings
        self.findings_list = []
        
        # Target text variations to search for (with or without formatting)
        self.search_patterns = [
            "**Leave Adjust Events and Due Dates unchecked**",
            "<strong>Leave Adjust Events and Due Dates unchecked</strong>",
            "Leave <strong>Adjust Events and Due Dates</strong> unchecked",
            "Leave Adjust Events and Due Dates unchecked",
            "Tick the 'Adjust Events and Due Dates' option. Select 'Remove Dates' for date adjustment.",
            "<li>Tick the '<strong>Adjust Events and Due Dates</strong>' option. Select '<strong>Remove Dates</strong>' for date adjustment.</li>",
            "<li>Leave Adjust Events and Due Dates unchecked</li>"
        ]
        
        # More generic search terms for broader identification
        self.generic_terms = [
            "Adjust Events and Due Dates",
            "Leave Adjust Events",
            "unchecked"
        ]
        
        self.logger.info("Initialized Canvas Syllabus Scanner tool")

    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> Union[List[Dict], Dict]:
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

    def get_terms(self, account_id: str = '1') -> List[Dict]:
        """Fetch all enrollment terms from Canvas."""
        api_url = f'{self.api_url}/accounts/{account_id}/terms'
        params = {'per_page': 100}
        
        try:
            response = requests.get(api_url, headers=self.headers, params=params)
            response.raise_for_status()
            terms_data = response.json()
            return terms_data.get('enrollment_terms', [])
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching terms: {str(e)}")
            raise Exception(f"Error fetching terms: {str(e)}")

    def get_courses(self, subaccount_id: str, term_id: Optional[str] = None) -> List[Dict]:
        """Fetch courses from a subaccount."""
        self.logger.info(f"Fetching courses from subaccount {subaccount_id}")
        if term_id:
            self.logger.info(f"Filtering by term ID: {term_id}")
        
        api_url = f"{self.api_url}/accounts/{subaccount_id}/courses"
        params = {
            'include[]': ['term'],
            'per_page': 100,
            'state[]': ['available', 'unpublished', 'completed', 'created']
        }
        
        if term_id:
            params['enrollment_term_id'] = term_id
        
        try:
            courses = []
            response = requests.get(api_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            while True:
                data = response.json()
                courses.extend(data)
                
                if 'next' not in response.links:
                    break
                    
                response = requests.get(response.links['next']['url'], headers=self.headers)
                response.raise_for_status()
                time.sleep(0.1)  # Small delay to avoid rate limits
            
            # Log workflow states for debugging
            workflow_states = {}
            for course in courses:
                state = course.get('workflow_state', 'unknown')
                workflow_states[state] = workflow_states.get(state, 0) + 1
            
            self.logger.info(f"Found {len(courses)} courses with workflow states: {workflow_states}")
            print(f"Found {len(courses)} courses with workflow states: {workflow_states}")
            
            return courses
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching courses: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def scan_syllabus(self, course_id: str) -> Tuple[bool, List[str], str]:
        """
        Scan syllabus content for target text.
        Returns (found_any, matched_patterns, error_message).
        """
        url = f"{self.api_url}/courses/{course_id}"
        params = {'include[]': 'syllabus_body'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'syllabus_body' not in data or not data['syllabus_body']:
                return False, [], "Syllabus is empty"
                
            syllabus = data['syllabus_body']
            matched_patterns = []
            
            # First check for exact matches with our search patterns
            for pattern in self.search_patterns:
                if pattern in syllabus:
                    matched_patterns.append(f"Exact: {pattern}")
            
            # If no exact matches, try more generic terms
            if not matched_patterns:
                for term in self.generic_terms:
                    if term in syllabus:
                        matched_patterns.append(f"Generic: {term}")
            
            # If still no matches, try with BeautifulSoup to find list items
            if not matched_patterns:
                soup = BeautifulSoup(syllabus, 'html.parser')
                list_items = soup.find_all('li')
                for li in list_items:
                    li_text = li.get_text().lower()
                    if "adjust events" in li_text and "unchecked" in li_text:
                        matched_patterns.append(f"List item: {li_text[:75]}...")
            
            # If we found any matches
            found_any = len(matched_patterns) > 0
            return found_any, matched_patterns, ""
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching syllabus: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg

    def process_course(self, course: Dict) -> Dict:
        """
        Process a single course to scan syllabus.
        Returns result dictionary with scan information.
        """
        course_id = str(course['id'])
        course_name = course.get('name', 'Unknown')
        term_name = course.get('term', {}).get('name', 'Unknown Term')
        workflow_state = course.get('workflow_state', 'unknown')
        
        self.logger.info(f"Scanning course {course_id}: {course_name} (State: {workflow_state})")
        
        result = {
            'Course ID': course_id,
            'Course Name': course_name,
            'Term Name': term_name,
            'Workflow State': workflow_state,
            'Found Text': 'No',
            'Matched Patterns': '',
            'Canvas URL': f"{self.base_url}/courses/{course_id}"
        }
        
        # Scan syllabus content
        found, matched_patterns, error = self.scan_syllabus(course_id)
        
        if error:
            result['Found Text'] = 'Error'
            result['Matched Patterns'] = error
            return result
            
        if found:
            result['Found Text'] = 'Yes'
            result['Matched Patterns'] = '; '.join(matched_patterns)
            
        return result

    def process_courses(self, courses: List[Dict]) -> None:
        """Process a list of courses with parallel execution."""
        if not courses:
            print("No courses to process.")
            return
            
        print(f"Scanning {len(courses)} courses...")
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_course = {executor.submit(self.process_course, course): course 
                               for course in courses}
            
            completed = 0
            total = len(courses)
            found_count = 0
            
            for future in concurrent.futures.as_completed(future_to_course):
                course = future_to_course[future]
                course_id = str(course['id'])
                course_name = course.get('name', 'Unknown')
                
                try:
                    result = future.result()
                    self.findings_list.append(result)
                    
                    completed += 1
                    status = "✓ Found" if result['Found Text'] == 'Yes' else "Not found"
                    if result['Found Text'] == 'Yes':
                        found_count += 1
                    
                    print(f"[{completed}/{total}] Course {course_id}: {status}")
                    
                except Exception as e:
                    self.logger.error(f"Error scanning course {course_id}: {str(e)}")
                    print(f"[{completed}/{total}] Error scanning course {course_id}: {str(e)}")
                    
                    self.findings_list.append({
                        'Course ID': course_id,
                        'Course Name': course_name,
                        'Term Name': course.get('term', {}).get('name', 'Unknown Term'),
                        'Workflow State': course.get('workflow_state', 'unknown'),
                        'Found Text': 'Error',
                        'Matched Patterns': str(e),
                        'Canvas URL': f"{self.base_url}/courses/{course_id}"
                    })
                    
                    completed += 1
            
            print(f"\nScan complete. Found target text in {found_count} out of {total} courses.")

    def process_single_course(self, course_id: str) -> None:
        """Process a single course by ID."""
        try:
            # Get course details
            course_info = self.make_request(f"courses/{course_id}")
            result = self.process_course(course_info)
            self.findings_list.append(result)
            
            status = "✓ Found" if result['Found Text'] == 'Yes' else "Not found"
            print(f"Course {course_id}: {status}")
            if result['Found Text'] == 'Yes':
                print(f"Matched: {result['Matched Patterns']}")
            
        except Exception as e:
            self.logger.error(f"Error scanning course {course_id}: {str(e)}")
            print(f"Error scanning course {course_id}: {str(e)}")

    def generate_report(self) -> str:
        """Generate report of all scanned courses."""
        if not self.findings_list:
            print("No data to report.")
            return ""
        
        df = pd.DataFrame(self.findings_list)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'syllabus_scan_report_{timestamp}.xlsx'
        
        # Add hyperlink formula for Excel
        df['Canvas Link'] = df['Canvas URL'].apply(
            lambda x: f'=HYPERLINK("{x}","Open in Canvas")'
        )
        
        # Sort by whether text was found
        df = df.sort_values(by=['Found Text', 'Term Name', 'Course Name'], 
                           ascending=[False, True, True])
        
        # Write to Excel
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Scan Results')
            
            # Format hyperlinks
            workbook = writer.book
            worksheet = writer.sheets['Scan Results']
            link_format = workbook.add_format({'color': 'blue', 'underline': True})
            
            # Apply format to hyperlink column
            col_idx = df.columns.get_loc('Canvas Link')
            for row in range(1, len(df) + 1):
                worksheet.write_formula(row, col_idx, df.iloc[row-1]['Canvas Link'], link_format)
        
        # Generate summary
        total = len(df)
        found = sum(1 for status in df['Found Text'] if status == 'Yes')
        not_found = sum(1 for status in df['Found Text'] if status == 'No')
        errors = sum(1 for status in df['Found Text'] if status == 'Error')
        
        print(f"\nSummary:")
        print(f"  Total courses scanned: {total}")
        print(f"  Text found: {found}")
        print(f"  Text not found: {not_found}")
        print(f"  Errors: {errors}")
        print(f"  Report file: {filename}")
        
        # Print results by workflow state
        workflow_stats = df.groupby(['Workflow State', 'Found Text']).size().unstack(fill_value=0)
        print("\nResults by workflow state:")
        print(workflow_stats)
        
        return filename

def main():
    print("\nCanvas Syllabus Scanner - Find Only Version")
    print("=" * 60)
    print("\nThis tool scans Canvas course syllabi for variants of the")
    print("'Adjust Events and Due Dates' instruction without making any changes.")
    print("=" * 60)
    
    # Get user input
    base_url = input("\nEnter your Canvas URL (e.g., aculeo.beta.instructure.com): ").strip()
    api_token = input("Enter your Canvas API token: ").strip()
    
    # Initialize tool
    scanner = CanvasSyllabusScanner(base_url, api_token)
    
    # Ask for single course or subaccount
    mode = input("\nScan a single course (1) or courses in a subaccount (2)? (1/2): ").strip()
    
    if mode == '1':
        # Single course mode
        course_id = input("Enter course ID: ").strip()
        
        print(f"\nReady to scan course {course_id}.")
        confirm = input("Proceed? (y/n): ").strip().lower() == 'y'
        
        if confirm:
            scanner.process_single_course(course_id)
            scanner.generate_report()
        else:
            print("Operation cancelled.")
            
    else:
        # Subaccount mode
        subaccount_id = input("Enter subaccount ID: ").strip()
        
        # Term filtering
        use_term = input("\nFilter by term? (y/n): ").strip().lower() == 'y'
        term_id = None
        
        if use_term:
            try:
                terms = scanner.get_terms()
                
                if terms:
                    print("\nAvailable terms:")
                    for i, term in enumerate(terms, 1):
                        print(f"{i}. {term['name']} (ID: {term['id']})")
                    
                    term_choice = input("\nEnter term number: ").strip()
                    if term_choice.isdigit() and 1 <= int(term_choice) <= len(terms):
                        term_id = terms[int(term_choice) - 1]['id']
                        print(f"Selected term: {terms[int(term_choice) - 1]['name']}")
                else:
                    print("No terms found.")
            except Exception as e:
                print(f"Error getting terms: {str(e)}")
                print("Proceeding without term filtering.")
        
        # Get courses
        try:
            courses = scanner.get_courses(subaccount_id, term_id)
            
            if not courses:
                print("No courses found matching the criteria.")
                return
                
            print(f"\nReady to scan {len(courses)} courses.")
            confirm = input("Proceed? (y/n): ").strip().lower() == 'y'
            
            if confirm:
                # Process courses and generate report
                scanner.process_courses(courses)
                scanner.generate_report()
            else:
                print("Operation cancelled.")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()