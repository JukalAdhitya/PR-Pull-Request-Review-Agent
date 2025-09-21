import os
from typing import Optional, List
from datetime import datetime
import requests
from src.models.pull_request import PullRequest

class BitbucketConnector:
    """Connector for Bitbucket API using REST API"""
    
    def __init__(self, username: Optional[str] = None, app_password: Optional[str] = None):
        """Initialize Bitbucket connector with username and app password"""
        self.username = username or os.getenv('BITBUCKET_USERNAME')
        self.app_password = app_password or os.getenv('BITBUCKET_APP_PASSWORD')
        self.base_url = "https://api.bitbucket.org/2.0"
        
        # Set up authentication
        if self.username and self.app_password:
            self.auth = (self.username, self.app_password)
        else:
            self.auth = None
    
    def get_pull_request(self, repo_url: str, pr_number: int) -> Optional[PullRequest]:
        """
        Fetch pull request data from Bitbucket
        
        Args:
            repo_url: Bitbucket repository URL (e.g., 'owner/repo' or full URL)
            pr_number: Pull request number
            
        Returns:
            PullRequest object or None if not found
        """
        try:
            # Extract workspace and repo from URL
            workspace, repo_slug = self._extract_workspace_repo(repo_url)
            if not workspace or not repo_slug:
                raise ValueError(f"Invalid repository URL: {repo_url}")
            
            # Get pull request data
            pr_url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_number}"
            response = requests.get(pr_url, auth=self.auth)
            
            if response.status_code == 404:
                print(f"Pull request #{pr_number} not found")
                return None
            elif response.status_code != 200:
                print(f"Bitbucket API error: {response.status_code} - {response.text}")
                return None
            
            pr_data = response.json()
            
            # Get files changed
            files_changed = []
            try:
                diff_url = f"{pr_url}/diff"
                diff_response = requests.get(diff_url, auth=self.auth)
                if diff_response.status_code == 200:
                    # Parse diff to extract file changes
                    files_changed = self._parse_diff_files(diff_response.text)
            except Exception as e:
                print(f"Warning: Could not fetch file changes: {e}")
            
            # Get commits count
            commits_count = 0
            try:
                commits_url = f"{pr_url}/commits"
                commits_response = requests.get(commits_url, auth=self.auth)
                if commits_response.status_code == 200:
                    commits_data = commits_response.json()
                    commits_count = commits_data.get('size', 0)
            except Exception as e:
                print(f"Warning: Could not fetch commits count: {e}")
            
            # Create PullRequest object
            pull_request = PullRequest(
                id=str(pr_data.get('id', '')),
                title=pr_data.get('title', ''),
                description=pr_data.get('description', '') or '',
                author=pr_data.get('author', {}).get('display_name', ''),
                source_branch=pr_data.get('source', {}).get('branch', {}).get('name', ''),
                target_branch=pr_data.get('destination', {}).get('branch', {}).get('name', ''),
                status=self._get_pr_status(pr_data),
                created_at=self._parse_datetime(pr_data.get('created_on')),
                updated_at=self._parse_datetime(pr_data.get('updated_on')),
                platform='bitbucket',
                repository_url=pr_data.get('links', {}).get('html', {}).get('href', '').replace(f'/pullrequests/{pr_number}', ''),
                pr_url=pr_data.get('links', {}).get('html', {}).get('href', ''),
                files_changed=files_changed,
                additions=pr_data.get('additions', 0),
                deletions=pr_data.get('deletions', 0),
                commits_count=commits_count,
                labels=[],  # Bitbucket doesn't have labels in the same way
                assignees=[],  # Would need additional API call
                reviewers=[]  # Would need additional API call
            )
            
            return pull_request
            
        except Exception as e:
            print(f"Error fetching PR: {e}")
            return None
    
    def add_review_comment(self, repo_url: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> bool:
        """
        Add a review comment to a pull request
        
        Args:
            repo_url: Bitbucket repository URL
            pr_number: Pull request number
            comment: Comment text
            file_path: File path for inline comment (optional)
            line_number: Line number for inline comment (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            workspace, repo_slug = self._extract_workspace_repo(repo_url)
            if not workspace or not repo_slug:
                return False
            
            # Create comment
            comment_url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_number}/comments"
            
            comment_data = {
                'content': {
                    'raw': comment
                }
            }
            
            # Add inline comment if file_path and line_number are provided
            if file_path and line_number:
                comment_data['inline'] = {
                    'path': file_path,
                    'to': line_number
                }
            
            response = requests.post(comment_url, json=comment_data, auth=self.auth)
            
            if response.status_code == 201:
                return True
            else:
                print(f"Error adding comment: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def _extract_workspace_repo(self, repo_url: str) -> tuple[Optional[str], Optional[str]]:
        """Extract workspace and repository from Bitbucket URL"""
        if repo_url.startswith('https://bitbucket.org/'):
            # Full URL: https://bitbucket.org/workspace/repo
            parts = repo_url.replace('https://bitbucket.org/', '').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif '/' in repo_url and not repo_url.startswith('http'):
            # Already in workspace/repo format
            parts = repo_url.split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        
        return None, None
    
    def _get_pr_status(self, pr_data: dict) -> str:
        """Determine PR status from Bitbucket data"""
        state = pr_data.get('state', '').lower()
        if state == 'merged':
            return 'merged'
        elif state == 'declined':
            return 'closed'
        elif state == 'open':
            return 'open'
        else:
            return 'unknown'
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse Bitbucket datetime string"""
        if not datetime_str:
            return None
        try:
            # Bitbucket uses ISO format: 2023-01-01T12:00:00.000000+00:00
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return None
    
    def _parse_diff_files(self, diff_content: str) -> List[dict]:
        """Parse diff content to extract file changes"""
        files_changed = []
        current_file = None
        
        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                # New file section
                if current_file:
                    files_changed.append(current_file)
                
                # Extract filename
                parts = line.split()
                if len(parts) >= 4:
                    old_file = parts[2].replace('a/', '')
                    new_file = parts[3].replace('b/', '')
                    current_file = {
                        'filename': new_file or old_file,
                        'status': 'renamed' if old_file != new_file else 'modified',
                        'additions': 0,
                        'deletions': 0,
                        'patch': ''
                    }
            elif line.startswith('new file mode'):
                if current_file:
                    current_file['status'] = 'added'
            elif line.startswith('deleted file mode'):
                if current_file:
                    current_file['status'] = 'deleted'
            elif current_file and line.startswith('+'):
                current_file['additions'] += 1
            elif current_file and line.startswith('-'):
                current_file['deletions'] += 1
        
        # Add the last file
        if current_file:
            files_changed.append(current_file)
        
        return files_changed
    
    def test_connection(self) -> bool:
        """Test Bitbucket API connection"""
        try:
            if self.auth:
                # Test with user info
                user_url = f"{self.base_url}/user"
                response = requests.get(user_url, auth=self.auth)
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"Connected to Bitbucket as: {user_data.get('display_name', 'Unknown')}")
                    return True
            else:
                # Test with a public repository
                test_url = f"{self.base_url}/repositories/atlassian/bitbucket"
                response = requests.get(test_url)
                if response.status_code == 200:
                    print("Connected to Bitbucket (anonymous)")
                    return True
            
            return False
        except Exception as e:
            print(f"Bitbucket connection failed: {e}")
            return False
