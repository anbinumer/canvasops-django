"""
Canvas Syllabus Targeted Fix

This script updates the 'Adjust Events and Due Dates' instruction in Canvas syllabi
with enhanced detection and replacement logic to match the scan report findings.
"""

import requests
from typing import Optional, Dict, List, Tuple, Union, Any
import logging
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import pytz
import re
import concurrent.futures
import time
import os

class CanvasSyllabusEnhancedFix:
    def __init__(self, base_url: str, api_token: str):
        """Initialize the Canvas Syllabus Enhanced Fix tool."""
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
                logging.FileHandler('syllabus_enhanced_fix.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize list to store findings
        self.findings_list = []
        
        # Target text patterns - both raw strings and compiled regex patterns
        self.old_text_variations = [
            "**Leave Adjust Events and Due Dates unchecked**",
            "<strong>Leave Adjust Events and Due Dates unchecked</strong>",
            "Leave <strong>Adjust Events and Due Dates</strong> unchecked",
            "Leave Adjust Events and Due Dates unchecked",
            "leave adjust events and due dates unchecked",
            "Tick the 'Adjust Events and Due Dates' option. Select 'Remove Dates' for date adjustment."
        ]
        
        # Regex patterns for more flexible matching
        self.regex_patterns = [
            re.compile(r"[Ll]eave\s+(?:<strong>)?[Aa]djust\s+[Ee]vents\s+and\s+[Dd]ue\s+[Dd]ates(?:</strong>)?\s+unchecked", re.IGNORECASE),
            re.compile(r"[Ll]eave\s+[Aa]djust\s+[Ee]vents(?:</strong>)?\s+unchecked", re.IGNORECASE),
            re.compile(r"[Tt]ick\s+the\s+'(?:<strong>)?[Aa]djust\s+[Ee]vents\s+and\s+[Dd]ue\s+[Dd]ates(?:</strong>)?'\s+option", re.IGNORECASE)
        ]
        
        # New text (formatted exactly as required)
        self.new_text_md = "Tick the '**Adjust Events and Due Dates**' option. Select '**Remove Dates**' for date adjustment."
        self.new_text_html = "Tick the '<strong>Adjust Events and Due Dates</strong>' option. Select '<strong>Remove Dates</strong>' for date adjustment."
        
        # Flag to enable debug mode (saves HTML content)
        self.debug_mode = False
        self.debug_dir = "debug_syllabus_fix"
        if self.debug_mode:
            os.makedirs(self.debug_dir, exist_ok=True)
            
        self.logger.info("Initialized Canvas Syllabus Enhanced Fix tool")

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

    def get_course(self, course_id: str) -> Dict:
        """Get details for a specific course."""
        try:
            course = self.make_request(f"courses/{course_id}")
            return course
        except Exception as e:
            self.logger.error(f"Error fetching course {course_id}: {str(e)}")
            raise

    def get_syllabus(self, course_id: str) -> Tuple[bool, str, Dict, List[str]]:
        """
        Fetch syllabus content for a given course.
        Returns (success, content, course_data, matched_patterns).
        """
        url = f"{self.api_url}/courses/{course_id}"
        params = {'include[]': 'syllabus_body'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'syllabus_body' not in data or not data['syllabus_body']:
                return False, "", data, []
                
            syllabus = data['syllabus_body']
            
            # Save original content for debugging
            if self.debug_mode:
                with open(os.path.join(self.debug_dir, f"original_{course_id}.html"), "w", encoding="utf-8") as f:
                    f.write(syllabus)
            
            # Check for matches using different methods
            matched_patterns = []
            
            # Method 1: Direct string matching
            for pattern in self.old_text_variations:
                if pattern in syllabus:
                    matched_patterns.append(f"Direct: {pattern[:30]}...")
            
            # Method 2: Regex matching
            for regex in self.regex_patterns:
                if regex.search(syllabus):
                    matched_patterns.append(f"Regex: {regex.pattern[:30]}...")
            
            # Method 3: Check list items with BeautifulSoup
            if not matched_patterns:
                soup = BeautifulSoup(syllabus, 'html.parser')
                list_items = soup.find_all('li')
                for li in list_items:
                    li_text = li.get_text().lower()
                    if ("adjust events" in li_text and "unchecked" in li_text) or \
                       ("leave adjust" in li_text) or \
                       ("adjust" in li_text and "events" in li_text and "unchecked" in li_text):
                        matched_patterns.append(f"List item: {li_text[:30]}...")
            
            return True, syllabus, data, matched_patterns
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching syllabus: {str(e)}"
            self.logger.error(error_msg)
            return False, "", {}, []

    def update_syllabus_content(self, course_id: str, syllabus_content: str, matched_patterns: List[str]) -> Tuple[str, int]:
        """
        Update the syllabus content with the properly formatted text.
        Returns (updated_content, number_of_replacements).
        """
        replacements = 0
        updated_content = syllabus_content
        
        # Save a copy of the original content for comparison
        original_content = syllabus_content
        
        # Method 1: Direct string replacement for exact matches
        for pattern in self.old_text_variations:
            if pattern in updated_content:
                self.logger.info(f"Direct replace - Course {course_id}: '{pattern[:30]}...'")
                updated_content = updated_content.replace(pattern, self.new_text_html)
                replacements += 1
        
        # Method 2: Regex replacement
        if replacements == 0:
            for regex in self.regex_patterns:
                updated_content, count = regex.subn(self.new_text_html, updated_content)
                if count > 0:
                    self.logger.info(f"Regex replace - Course {course_id}: {count} matches")
                    replacements += count
        
        # Method 3: Parse and modify HTML structure
        if replacements == 0:
            soup = BeautifulSoup(updated_content, 'html.parser')
            
            # First check list items
            list_items = soup.find_all('li')
            for li in list_items:
                li_text = li.get_text().lower()
                li_html = str(li)
                
                if any(term in li_text for term in ["adjust events", "leave adjust", "events and due dates"]) and \
                   "unchecked" in li_text:
                    self.logger.info(f"List item replace - Course {course_id}: '{li_text[:30]}...'")
                    new_li = soup.new_tag('li')
                    new_li.append(BeautifulSoup(self.new_text_html, 'html.parser'))
                    li.replace_with(new_li)
                    replacements += 1
            
            # If we made changes, convert back to string
            if replacements > 0:
                updated_content = str(soup)
        
        # Debug: Save the updated content if changes were made
        if self.debug_mode and replacements > 0:
            with open(os.path.join(self.debug_dir, f"updated_{course_id}.html"), "w", encoding="utf-8") as f:
                f.write(updated_content)
        
        # Check if we actually made any changes by comparing content
        if updated_content == original_content:
            if matched_patterns:
                self.logger.warning(f"Content matched but no replacements made for course {course_id}")
                self.logger.warning(f"Matched patterns: {matched_patterns}")
                
                # Last resort approach: If we found matches but couldn't replace normally,
                # try aggressive HTML manipulation
                soup = BeautifulSoup(updated_content, 'html.parser')
                
                # Find any list items that might contain our target text
                list_items = soup.find_all('li')
                for i, li in enumerate(list_items):
                    li_text = li.get_text().lower()
                    # Very broad matching to catch any potential instances
                    if ("adjust" in li_text and "events" in li_text) or \
                       ("events" in li_text and "unchecked" in li_text):
                        self.logger.info(f"Aggressive replace - Course {course_id}: list item {i}")
                        new_li = soup.new_tag('li')
                        new_li.append(BeautifulSoup(self.new_text_html, 'html.parser'))
                        li.replace_with(new_li)
                        replacements += 1
                
                if replacements > 0:
                    updated_content = str(soup)
                    
                    # Debug: Save the aggressively updated content
                    if self.debug_mode:
                        with open(os.path.join(self.debug_dir, f"aggressive_{course_id}.html"), "w", encoding="utf-8") as f:
                            f.write(updated_content)
            else:
                self.logger.info(f"No matching content found for course {course_id}")
                return updated_content, 0
        
        return updated_content, replacements

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
                verified_content = verify_data['syllabus_body'].lower()
                search_text_lower = self.new_text_html.lower()
                
                if search_text_lower in verified_content:
                    self.logger.info(f"Verification successful for course {course_id}")
                    return True
                else:
                    self.logger.warning(f"Update was submitted but verification failed for course {course_id}")
                    
                    # Debug: Save the verification content
                    if self.debug_mode:
                        with open(os.path.join(self.debug_dir, f"verification_{course_id}.html"), "w", encoding="utf-8") as f:
                            f.write(verify_data['syllabus_body'])
                    
                    return False
            else:
                self.logger.warning(f"Could not verify update for course {course_id}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error updating syllabus for course {course_id}: {str(e)}")
            return False

    def fix_course(self, course_id: str, pattern_info: str = None) -> Dict:
        """
        Process a single course to update syllabus instructions.
        Returns result dictionary with status information.
        """
        try:
            # Get course details and syllabus
            success, syllabus_content, course_data, matched_patterns = self.get_syllabus(course_id)
            
            # Extract course details
            course_name = course_data.get('name', 'Unknown')
            term_name = course_data.get('term', {}).get('name', 'Unknown Term')
            workflow_state = course_data.get('workflow_state', 'unknown')
            
            self.logger.info(f"Processing course {course_id}: {course_name} (State: {workflow_state})")
            
            result = {
                'Course ID': course_id,
                'Course Name': course_name,
                'Term Name': term_name,
                'Workflow State': workflow_state,
                'Status': 'Not processed',
                'Replacements': 0,
                'Matched Patterns': pattern_info or ', '.join(matched_patterns),
                'Canvas URL': f"{self.base_url}/courses/{course_id}"
            }
            
            if not success or not syllabus_content:
                result['Status'] = "Error: Empty syllabus"
                return result
                
            # Update syllabus content
            updated_content, replacements = self.update_syllabus_content(
                course_id, syllabus_content, matched_patterns)
                
            result['Replacements'] = replacements
            
            if replacements == 0:
                result['Status'] = "No replacements possible - content not found or already updated"
                return result
            
            # Send updated content to Canvas
            update_success = self.update_syllabus_in_canvas(course_id, updated_content)
            
            if update_success:
                result['Status'] = "Successfully updated"
            else:
                result['Status'] = "Failed to update in Canvas"
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing course {course_id}: {str(e)}")
            return {
                'Course ID': course_id,
                'Course Name': 'Error',
                'Term Name': 'Error',
                'Workflow State': 'Error',
                'Status': f"Error: {str(e)}",
                'Replacements': 0,
                'Matched Patterns': '',
                'Canvas URL': f"{self.base_url}/courses/{course_id}"
            }

    def process_excel_file(self, excel_file: str) -> pd.DataFrame:
        """Read the scan report Excel file and return the data."""
        try:
            # Read the Excel file
            df = pd.read_excel(excel_file)
            self.logger.info(f"Read {len(df)} rows from {excel_file}")
            return df
        except Exception as e:
            self.logger.error(f"Error reading Excel file: {str(e)}")
            raise

    def fix_courses_from_excel(self, excel_file: str, fix_only_found: bool = True) -> None:
        """Process courses from an Excel scan report."""
        try:
            # Read the Excel file
            df = self.process_excel_file(excel_file)
            
            # Filter for courses where text was found
            if fix_only_found:
                courses_to_fix = df[df['Found Text'] == 'Yes']
            else:
                courses_to_fix = df
                
            if len(courses_to_fix) == 0:
                print("No courses to fix in the Excel file.")
                return
                
            # Extract course IDs and matched patterns
            courses_to_fix = courses_to_fix[['Course ID', 'Matched Patterns']]
            
            print(f"Preparing to fix {len(courses_to_fix)} courses from the Excel file.")
            
            # Process a small batch first to check success rate
            sample_size = min(5, len(courses_to_fix))
            sample_df = courses_to_fix.head(sample_size)
            
            print(f"\nProcessing {sample_size} sample courses first to verify approach...")
            
            # Fix sample courses
            for _, row in sample_df.iterrows():
                course_id = str(row['Course ID'])
                pattern_info = row.get('Matched Patterns', '')
                
                result = self.fix_course(course_id, pattern_info)
                self.findings_list.append(result)
                print(f"Sample course {course_id}: {result['Status']}")
            
            # Check success rate
            sample_success = sum(1 for r in self.findings_list if r['Status'] == 'Successfully updated')
            print(f"\nSample success rate: {sample_success}/{sample_size}")
            
            # Ask if user wants to continue with the rest
            if sample_size < len(courses_to_fix):
                continue_processing = input("\nContinue with remaining courses? (y/n): ").strip().lower() == 'y'
                
                if not continue_processing:
                    print("Operation cancelled after sample processing.")
                    return
                
                # Process the rest of the courses
                remaining_df = courses_to_fix.iloc[sample_size:]
                
                # Fix remaining courses in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {}
                    for _, row in remaining_df.iterrows():
                        course_id = str(row['Course ID'])
                        pattern_info = row.get('Matched Patterns', '')
                        
                        futures[executor.submit(self.fix_course, course_id, pattern_info)] = course_id
                    
                    completed = 0
                    total = len(remaining_df)
                    
                    for future in concurrent.futures.as_completed(futures):
                        course_id = futures[future]
                        
                        try:
                            result = future.result()
                            self.findings_list.append(result)
                            
                            completed += 1
                            print(f"[{completed}/{total}] Course {course_id}: {result['Status']}")
                            
                        except Exception as e:
                            self.logger.error(f"Error fixing course {course_id}: {str(e)}")
                            print(f"[{completed}/{total}] Error fixing course {course_id}: {str(e)}")
                            
                            self.findings_list.append({
                                'Course ID': course_id,
                                'Course Name': 'Error',
                                'Term Name': 'Unknown',
                                'Workflow State': 'unknown',
                                'Status': f"Error: {str(e)}",
                                'Replacements': 0,
                                'Canvas URL': f"{self.base_url}/courses/{course_id}"
                            })
                            
                            completed += 1
            
        except Exception as e:
            self.logger.error(f"Error processing Excel file: {str(e)}")
            print(f"Error processing Excel file: {str(e)}")

    def enable_debug_mode(self):
        """Enable debug mode to save HTML content."""
        self.debug_mode = True
        os.makedirs(self.debug_dir, exist_ok=True)
        self.logger.info("Debug mode enabled")

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
        
        # Sort by success status
        df = df.sort_values(by=['Status', 'Term Name', 'Course Name'])
        
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
                worksheet.write_formula(row, col_idx, df.iloc[row-1]['Canvas Link'], link_format)
        
        # Generate summary
        total = len(df)
        updated = sum(1 for status in df['Status'] if status == 'Successfully updated')
        not_found = sum(1 for status in df['Status'] if "No replacements" in status)
        errors = sum(1 for status in df['Status'] if "Error" in status)
        
        print(f"\nSummary:")
        print(f"  Total courses processed: {total}")
        print(f"  Successfully updated: {updated}")
        print(f"  Text not found or already updated: {not_found}")
        print(f"  Errors: {errors}")
        print(f"  Report file: {filename}")
        
        return filename

def main():
    print("\nCanvas Syllabus Targeted Fix - Enhanced Version")
    print("=" * 70)
    print("\nThis tool updates the 'Adjust Events and Due Dates' instruction")
    print("with enhanced detection and replacement logic to match scan report findings.")
    print("=" * 70)
    
    # Get user input
    base_url = input("\nEnter your Canvas URL (e.g., aculeo.beta.instructure.com): ").strip()
    api_token = input("Enter your Canvas API token: ").strip()
    
    # Initialize tool
    fixer = CanvasSyllabusEnhancedFix(base_url, api_token)
    
    # Ask about debug mode
    debug_mode = input("\nEnable debug mode? This will save HTML content for troubleshooting (y/n): ").strip().lower() == 'y'
    if debug_mode:
        fixer.enable_debug_mode()
    
    # Get Excel file path
    excel_file = input("\nEnter the path to the scan report Excel file: ").strip()
    if not os.path.exists(excel_file):
        print(f"Error: File {excel_file} not found.")
        return
        
    # Ask if they want to fix only courses with found text or all courses
    fix_option = input("\nFix only courses where text was found (1) or all courses in the report (2)? (1/2): ").strip()
    fix_only_found = fix_option != '2'
    
    print(f"\nReady to process courses from {excel_file}.")
    confirm = input("Proceed? (y/n): ").strip().lower() == 'y'
    
    if confirm:
        # Process courses from Excel
        fixer.fix_courses_from_excel(excel_file, fix_only_found)
        fixer.generate_report()
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()