"""
Canvas Syllabus Text Content Fix

This script updates the 'Adjust Events and Due Dates' instruction in Canvas syllabi
by focusing only on the text content, regardless of HTML tags or structure.
"""

import requests
from typing import Optional, Dict, List, Tuple, Union
import logging
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import concurrent.futures
import time
import os

class CanvasSyllabusTextFix:
    def __init__(self, base_url: str, api_token: str):
        """Initialize the Canvas Syllabus Text Content Fix tool."""
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
                logging.FileHandler('syllabus_text_fix.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize list to store findings
        self.findings_list = []
        
        # Key text phrases to look for (regardless of HTML formatting)
        self.target_phrases = [
            "leave adjust events and due dates unchecked",
            "adjust events and due dates unchecked"
        ]
        
        # New text (formatted exactly as required)
        self.new_text_html = "Tick the '<strong>Adjust Events and Due Dates</strong>' option. Select '<strong>Remove Dates</strong>' for date adjustment."
        
        self.logger.info("Initialized Canvas Syllabus Text Content Fix tool")

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

    def get_syllabus(self, course_id: str) -> Tuple[bool, str, str, List[Dict]]:
        """
        Fetch syllabus content for a given course.
        Returns (success, content, error_message, found_items).
        """
        url = f"{self.api_url}/courses/{course_id}"
        params = {'include[]': 'syllabus_body'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'syllabus_body' not in data or not data['syllabus_body']:
                return False, "", "Syllabus is empty", []
                
            syllabus = data['syllabus_body']
            
            # Found items will contain the element, its position, and context
            found_items = []
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(syllabus, 'html.parser')
            
            # First, check all list items
            list_items = soup.find_all('li')
            for i, li in enumerate(list_items):
                li_text = li.get_text().lower()
                
                for phrase in self.target_phrases:
                    if phrase in li_text:
                        found_items.append({
                            'type': 'li',
                            'index': i,
                            'text': li_text,
                            'html': str(li),
                            'element': li
                        })
                        break
            
            # If not found in list items, check any elements with the text
            if not found_items:
                # Find any element containing our target phrases
                for phrase in self.target_phrases:
                    elements = soup.find_all(string=re.compile(phrase, re.IGNORECASE))
                    for element in elements:
                        found_items.append({
                            'type': 'text',
                            'text': element.strip(),
                            'html': str(element.parent),
                            'element': element.parent
                        })
            
            return True, syllabus, "", found_items
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching syllabus: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg, []

    def update_syllabus_content(self, syllabus_content: str, found_items: List[Dict]) -> Tuple[str, int]:
        """
        Update the syllabus content by replacing the target elements.
        Returns (updated_content, number_of_replacements).
        """
        if not found_items:
            return syllabus_content, 0
            
        soup = BeautifulSoup(syllabus_content, 'html.parser')
        replacements = 0
        
        for item in found_items:
            if item['type'] == 'li':
                # Handle list items by directly replacing the element
                element = item['element']
                new_li = soup.new_tag('li')
                new_li.append(BeautifulSoup(self.new_text_html, 'html.parser'))
                element.replace_with(new_li)
                replacements += 1
                self.logger.info(f"Replaced list item: {item['text'][:50]}...")
            
            elif item['type'] == 'text':
                # Find the nearest parent list item if available
                parent_li = item['element'].find_parent('li')
                
                if parent_li:
                    # Replace the whole list item
                    new_li = soup.new_tag('li')
                    new_li.append(BeautifulSoup(self.new_text_html, 'html.parser'))
                    parent_li.replace_with(new_li)
                else:
                    # Just replace the containing element
                    parent = item['element']
                    new_element = BeautifulSoup(self.new_text_html, 'html.parser')
                    parent.replace_with(new_element)
                
                replacements += 1
                self.logger.info(f"Replaced text: {item['text'][:50]}...")
        
        # Return the updated HTML if replacements were made
        if replacements > 0:
            return str(soup), replacements
        
        # If no replacements were made with BeautifulSoup, try basic text replacement
        # This is a fallback in case the soup parsing fails to identify replaceable elements
        for phrase in self.target_phrases:
            pattern = re.compile(r'<li>[^<]*' + re.escape(phrase) + r'[^<]*</li>', re.IGNORECASE)
            updated_content, count = pattern.subn(f"<li>{self.new_text_html}</li>", syllabus_content)
            
            if count > 0:
                self.logger.info(f"Replaced {count} instances using regex pattern")
                return updated_content, count
        
        return syllabus_content, replacements

    def update_syllabus_in_canvas(self, course_id: str, updated_content: str) -> bool:
        """Submit the updated syllabus content to Canvas."""
        url = f"{self.api_url}/courses/{course_id}"
        payload = {
            'course': {
                'syllabus_body': updated_content
            }
        }
        
        try:
            # Add a delay to avoid any rate limiting or processing issues
            time.sleep(0.5)
            
            self.logger.info(f"Updating syllabus for course {course_id}")
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Verify the update was successful by fetching the syllabus again
            time.sleep(0.5)  # Wait a moment for the update to process
            verify_response = requests.get(f"{self.api_url}/courses/{course_id}?include[]=syllabus_body", 
                                          headers=self.headers)
            verify_response.raise_for_status()
            
            verify_data = verify_response.json()
            if 'syllabus_body' in verify_data:
                # Check if new text is in the verified content (case insensitive)
                verify_text = verify_data['syllabus_body'].lower()
                search_terms = ["tick the", "adjust events and due dates", "remove dates"]
                
                # Check if all search terms are in the text
                if all(term in verify_text for term in search_terms):
                    self.logger.info(f"Verification successful for course {course_id}")
                    return True
                else:
                    self.logger.warning(f"Update was submitted but verification failed for course {course_id}")
                    return False
            else:
                self.logger.warning(f"Could not verify update for course {course_id}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error updating syllabus for course {course_id}: {str(e)}")
            return False

    def process_course(self, course: Dict) -> Dict:
        """
        Process a single course to update syllabus instructions.
        Returns result dictionary with status information.
        """
        course_id = str(course['id'])
        course_name = course.get('name', 'Unknown')
        term_name = course.get('term', {}).get('name', 'Unknown Term')
        workflow_state = course.get('workflow_state', 'unknown')
        
        self.logger.info(f"Processing course {course_id}: {course_name} (State: {workflow_state})")
        
        result = {
            'Course ID': course_id,
            'Course Name': course_name,
            'Term Name': term_name,
            'Workflow State': workflow_state,
            'Status': 'Not processed',
            'Items Found': 0,
            'Replacements': 0,
            'Canvas URL': f"{self.base_url}/courses/{course_id}"
        }
        
        # Step 1: Get syllabus content
        success, syllabus_content, error, found_items = self.get_syllabus(course_id)
        
        if not success:
            result['Status'] = f"Error: {error}"
            return result
            
        # Update items found
        result['Items Found'] = len(found_items)
        
        # Check if syllabus contains target text
        if not found_items:
            result['Status'] = "No target text found"
            return result
        
        # Step 2: Update syllabus content
        updated_content, replacements = self.update_syllabus_content(syllabus_content, found_items)
        result['Replacements'] = replacements
        
        if replacements == 0:
            result['Status'] = "No replacements made"
            return result
        
        # Step 3: Send updated content to Canvas
        update_success = self.update_syllabus_in_canvas(course_id, updated_content)
        
        if update_success:
            result['Status'] = "Successfully updated"
        else:
            result['Status'] = "Failed to update in Canvas"
            
        return result

    def process_courses(self, courses: List[Dict]) -> None:
        """Process a list of courses with parallel execution."""
        if not courses:
            print("No courses to process.")
            return
            
        print(f"Processing {len(courses)} courses...")
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_course = {executor.submit(self.process_course, course): course 
                               for course in courses}
            
            completed = 0
            total = len(courses)
            
            for future in concurrent.futures.as_completed(future_to_course):
                course = future_to_course[future]
                course_id = str(course['id'])
                course_name = course.get('name', 'Unknown')
                
                try:
                    result = future.result()
                    self.findings_list.append(result)
                    
                    completed += 1
                    print(f"[{completed}/{total}] Course {course_id}: {result['Status']}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing course {course_id}: {str(e)}")
                    print(f"[{completed}/{total}] Error processing course {course_id}: {str(e)}")
                    
                    self.findings_list.append({
                        'Course ID': course_id,
                        'Course Name': course_name,
                        'Term Name': course.get('term', {}).get('name', 'Unknown Term'),
                        'Workflow State': course.get('workflow_state', 'unknown'),
                        'Status': f"Error: {str(e)}",
                        'Items Found': 0,
                        'Replacements': 0,
                        'Canvas URL': f"{self.base_url}/courses/{course_id}"
                    })
                    completed += 1

    def process_excel_file(self, excel_file: str, fix_only_found: bool = True) -> None:
        """Process courses from an Excel scan report."""
        try:
            # Read the Excel file
            df = pd.read_excel(excel_file)
            self.logger.info(f"Read {len(df)} rows from {excel_file}")
            
            # Filter for courses where text was found
            if fix_only_found:
                courses_to_fix = df[df['Found Text'] == 'Yes']
            else:
                courses_to_fix = df
                
            if len(courses_to_fix) == 0:
                print("No courses to fix in the Excel file.")
                return
            
            course_ids = courses_to_fix['Course ID'].astype(str).tolist()
            print(f"Preparing to fix {len(course_ids)} courses from the Excel file.")
            
            # Fetch each course and process
            courses = []
            for course_id in course_ids:
                try:
                    course = self.make_request(f"courses/{course_id}")
                    courses.append(course)
                except Exception as e:
                    self.logger.error(f"Error fetching course {course_id}: {str(e)}")
                    print(f"Error fetching course {course_id}: {str(e)}")
            
            self.process_courses(courses)
            
        except Exception as e:
            self.logger.error(f"Error processing Excel file: {str(e)}")
            print(f"Error processing Excel file: {str(e)}")

    def process_single_course(self, course_id: str) -> None:
        """Process a single course by ID."""
        try:
            # Get course details
            course_info = self.make_request(f"courses/{course_id}")
            result = self.process_course(course_info)
            self.findings_list.append(result)
            
            print(f"Course {course_id}: {result['Status']}")
            print(f"Items found: {result['Items Found']}")
            print(f"Replacements made: {result['Replacements']}")
            
        except Exception as e:
            self.logger.error(f"Error processing course {course_id}: {str(e)}")
            print(f"Error processing course {course_id}: {str(e)}")

    def generate_report(self) -> str:
        """Generate report of all processed courses."""
        if not self.findings_list:
            print("No data to report.")
            return ""
        
        df = pd.DataFrame(self.findings_list)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'syllabus_fix_report_{timestamp}.xlsx'
        
        # Add hyperlink formula for Excel
        df['Canvas Link'] = df['Canvas URL'].apply(
            lambda x: f'=HYPERLINK("{x}","Open in Canvas")'
        )
        
        # Write to Excel
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Fix Results')
            
            # Format hyperlinks
            workbook = writer.book
            worksheet = writer.sheets['Fix Results']
            link_format = workbook.add_format({'color': 'blue', 'underline': True})
            
            # Apply format to hyperlink column
            col_idx = df.columns.get_loc('Canvas Link')
            for row in range(1, len(df) + 1):
                try:
                    worksheet.write_formula(row, col_idx, df.iloc[row-1]['Canvas Link'], link_format)
                except:
                    pass  # Skip if there's an issue with hyperlink formula
        
        # Generate summary
        total = len(df)
        items_found = sum(df['Items Found'])
        updated = sum(1 for status in df['Status'] if status == 'Successfully updated')
        not_found = sum(1 for status in df['Status'] if status == 'No target text found')
        errors = sum(1 for status in df['Status'] if "Error" in status)
        
        print(f"\nSummary:")
        print(f"  Total courses processed: {total}")
        print(f"  Total items found: {items_found}")
        print(f"  Successfully updated: {updated}")
        print(f"  Text not found: {not_found}")
        print(f"  Errors: {errors}")
        print(f"  Report file: {filename}")
        
        # Print results by workflow state
        workflow_stats = {}
        for r in self.findings_list:
            state = r.get('Workflow State', 'unknown')
            workflow_stats[state] = workflow_stats.get(state, 0) + 1
            
        print("\nResults by workflow state:")
        for state, count in workflow_stats.items():
            print(f"  {state}: {count} courses")
        
        return filename

def main():
    print("\nCanvas Syllabus Text Content Fix")
    print("=" * 65)
    print("\nThis tool updates the 'Adjust Events and Due Dates' instruction")
    print("by focusing on the text content, regardless of HTML structure.")
    print("=" * 65)
    
    # Get user input
    base_url = input("\nEnter your Canvas URL (e.g., aculeo.beta.instructure.com): ").strip()
    api_token = input("Enter your Canvas API token: ").strip()
    
    # Initialize tool
    fixer = CanvasSyllabusTextFix(base_url, api_token)
    
    # Ask for input method
    input_method = input("\nChoose input method:\n1. Process a single course\n2. Process courses in a subaccount\n3. Process courses from Excel file\nEnter choice (1-3): ").strip()
    
    if input_method == '1':
        # Single course mode
        course_id = input("\nEnter course ID: ").strip()
        
        print(f"\nReady to process course {course_id}.")
        confirm = input("Proceed? (y/n): ").strip().lower() == 'y'
        
        if confirm:
            fixer.process_single_course(course_id)
            fixer.generate_report()
        else:
            print("Operation cancelled.")
            
    elif input_method == '2':
        # Subaccount mode
        subaccount_id = input("\nEnter subaccount ID: ").strip()
        
        # Term filtering
        use_term = input("\nFilter by term? (y/n): ").strip().lower() == 'y'
        term_id = None
        
        if use_term:
            try:
                terms = fixer.get_terms()
                
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
            courses = fixer.get_courses(subaccount_id, term_id)
            
            if not courses:
                print("No courses found matching the criteria.")
                return
                
            print(f"\nReady to process {len(courses)} courses.")
            confirm = input("Proceed? (y/n): ").strip().lower() == 'y'
            
            if confirm:
                # Process courses and generate report
                fixer.process_courses(courses)
                fixer.generate_report()
            else:
                print("Operation cancelled.")
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    elif input_method == '3':
        # Excel file mode
        excel_file = input("\nEnter the path to the scan report Excel file: ").strip()
        
        if not os.path.exists(excel_file):
            print(f"Error: File {excel_file} not found.")
            return
            
        # Ask if they want to fix only courses where text was found or all courses
        fix_option = input("\nFix only courses where text was found (1) or all courses in the report (2)? (1/2): ").strip()
        fix_only_found = fix_option != '2'
        
        print(f"\nReady to process courses from {excel_file}.")
        confirm = input("Proceed? (y/n): ").strip().lower() == 'y'
        
        if confirm:
            # Process courses from Excel
            fixer.process_excel_file(excel_file, fix_only_found)
            fixer.generate_report()
        else:
            print("Operation cancelled.")
    
    else:
        print("Invalid choice. Please restart the script and select 1, 2, or 3.")

if __name__ == "__main__":
    main()