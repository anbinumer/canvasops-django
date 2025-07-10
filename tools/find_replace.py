import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple
import logging

class LTIFindReplaceService:
    def __init__(self, base_url, api_token, url_mappings, is_beta=False):
        self.base_url = f"https://{base_url.replace('https://', '')}".rstrip('/')
        if is_beta:
            self.base_url = self.base_url.replace('.instructure.com', '.beta.instructure.com')
        self.api_url = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.url_mappings = url_mappings
        self.logger = logging.getLogger(__name__)

    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        if params is None:
            params = {}
        params['per_page'] = 100
        url = f"{self.api_url}/{endpoint}"
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

    def update_content(self, course_id: str, content_type: str, content_id: str, new_content: str) -> Tuple[bool, str]:
        try:
            if content_type == 'syllabus':
                url = f"{self.api_url}/courses/{course_id}"
                payload = {'course': {'syllabus_body': new_content}}
            elif content_type == 'page':
                url = f"{self.api_url}/courses/{course_id}/pages/{content_id}"
                payload = {'wiki_page': {'body': new_content}}
            elif content_type == 'assignment':
                url = f"{self.api_url}/courses/{course_id}/assignments/{content_id}"
                payload = {'assignment': {'description': new_content}}
            elif content_type == 'quiz':
                url = f"{self.api_url}/courses/{course_id}/quizzes/{content_id}"
                payload = {'quiz': {'description': new_content}}
            elif content_type == 'discussion':
                url = f"{self.api_url}/courses/{course_id}/discussion_topics/{content_id}"
                payload = {'message': new_content}
            elif content_type == 'announcement':
                url = f"{self.api_url}/courses/{course_id}/discussion_topics/{content_id}"
                payload = {'message': new_content}
            else:
                return False, f"Unknown content type: {content_type}"
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return True, ""
        except requests.exceptions.RequestException as e:
            return False, str(e)

    def replace_urls_in_content(self, content: str) -> Tuple[str, List[Tuple[str, str]]]:
        if not content:
            return content, []
        replacements = []
        soup = BeautifulSoup(content, 'html.parser')
        # Replace URLs in href attributes
        for tag in soup.find_all(href=True):
            for old_url, new_url in self.url_mappings.items():
                if old_url in tag['href']:
                    replacements.append((old_url, new_url))
                    tag['href'] = tag['href'].replace(old_url, new_url)
        # Replace URLs in src attributes
        for tag in soup.find_all(src=True):
            for old_url, new_url in self.url_mappings.items():
                if old_url in tag['src']:
                    replacements.append((old_url, new_url))
                    tag['src'] = tag['src'].replace(old_url, new_url)
        # Replace URLs in text
        html = str(soup)
        for old_url, new_url in self.url_mappings.items():
            if old_url in html:
                html = html.replace(old_url, new_url)
                replacements.append((old_url, new_url))
        return html, replacements

    def scan_content(self, course_id: str, content_types: List[str], search_targets: List[str], preview_only=True) -> List[Dict]:
        findings = []
        # Syllabus
        if 'syllabus' in content_types:
            syllabus = self.make_request(f"courses/{course_id}", params={'include[]': 'syllabus_body'})
            if syllabus and syllabus.get('syllabus_body'):
                for target in search_targets:
                    if target in syllabus['syllabus_body']:
                        findings.append({
                            'content_type': 'syllabus',
                            'location': 'syllabus',
                            'match': target,
                            'preview': syllabus['syllabus_body']
                        })
                if not preview_only:
                    new_content, replacements = self.replace_urls_in_content(syllabus['syllabus_body'])
                    if replacements:
                        self.update_content(course_id, 'syllabus', '', new_content)
        # Pages
        if 'pages' in content_types:
            pages = self.make_request(f"courses/{course_id}/pages")
            for page in pages:
                page_detail = self.make_request(f"courses/{course_id}/pages/{page['url']}")
                if page_detail and page_detail.get('body'):
                    for target in search_targets:
                        if target in page_detail['body']:
                            findings.append({
                                'content_type': 'page',
                                'location': page_detail.get('html_url', ''),
                                'match': target,
                                'preview': page_detail['body']
                            })
                    if not preview_only:
                        new_content, replacements = self.replace_urls_in_content(page_detail['body'])
                        if replacements:
                            self.update_content(course_id, 'page', page['url'], new_content)
        # Assignments
        if 'assignments' in content_types:
            assignments = self.make_request(f"courses/{course_id}/assignments")
            for assignment in assignments:
                if assignment.get('description'):
                    for target in search_targets:
                        if target in assignment['description']:
                            findings.append({
                                'content_type': 'assignment',
                                'location': assignment.get('html_url', ''),
                                'match': target,
                                'preview': assignment['description']
                            })
                    if not preview_only:
                        new_content, replacements = self.replace_urls_in_content(assignment['description'])
                        if replacements:
                            self.update_content(course_id, 'assignment', assignment['id'], new_content)
        # Quizzes
        if 'quizzes' in content_types:
            quizzes = self.make_request(f"courses/{course_id}/quizzes")
            for quiz in quizzes:
                if quiz.get('description'):
                    for target in search_targets:
                        if target in quiz['description']:
                            findings.append({
                                'content_type': 'quiz',
                                'location': quiz.get('html_url', ''),
                                'match': target,
                                'preview': quiz['description']
                            })
                    if not preview_only:
                        new_content, replacements = self.replace_urls_in_content(quiz['description'])
                        if replacements:
                            self.update_content(course_id, 'quiz', quiz['id'], new_content)
        # Discussions
        if 'discussions' in content_types:
            discussions = self.make_request(f"courses/{course_id}/discussion_topics")
            for discussion in discussions:
                if discussion.get('message'):
                    for target in search_targets:
                        if target in discussion['message']:
                            findings.append({
                                'content_type': 'discussion',
                                'location': discussion.get('html_url', ''),
                                'match': target,
                                'preview': discussion['message']
                            })
                    if not preview_only:
                        new_content, replacements = self.replace_urls_in_content(discussion['message'])
                        if replacements:
                            self.update_content(course_id, 'discussion', discussion['id'], new_content)
        # Announcements
        if 'announcements' in content_types:
            announcements = self.make_request(f"courses/{course_id}/discussion_topics?only_announcements=true")
            for announcement in announcements:
                if announcement.get('message'):
                    for target in search_targets:
                        if target in announcement['message']:
                            findings.append({
                                'content_type': 'announcement',
                                'location': announcement.get('html_url', ''),
                                'match': target,
                                'preview': announcement['message']
                            })
                    if not preview_only:
                        new_content, replacements = self.replace_urls_in_content(announcement['message'])
                        if replacements:
                            self.update_content(course_id, 'announcement', announcement['id'], new_content)
        return findings 