import os
from typing import Optional, List
from datetime import datetime
import gitlab
from src.models.pull_request import PullRequest

class GitLabConnector:
    """Connector for GitLab API using python-gitlab"""
    
    def __init__(self, access_token: Optional[str] = None, gitlab_url: str = "https://gitlab.com"):
        """Initialize GitLab connector with access token and GitLab instance URL"""
        self.access_token = access_token or os.getenv('GITLAB_TOKEN')
        self.gitlab_url = gitlab_url
        
        if self.access_token:
            self.gitlab = gitlab.Gitlab(gitlab_url, private_token=self.access_token)
        else:
            # Use unauthenticated access (limited rate)
            self.gitlab = gitlab.Gitlab(gitlab_url)
    
    def get_pull_request(self, repo_url: str, mr_number: int) -> Optional[PullRequest]:
        """
        Fetch merge request data from GitLab
        
        Args:
            repo_url: GitLab repository URL (e.g., 'owner/repo' or full URL)
            mr_number: Merge request number
            
        Returns:
            PullRequest object or None if not found
        """
        try:
            # Extract project path from URL
            project_path = self._extract_project_path(repo_url)
            if not project_path:
                raise ValueError(f"Invalid repository URL: {repo_url}")
            
            # Get project and merge request
            try:
                project = self.gitlab.projects.get(project_path)
            except gitlab.exceptions.GitlabGetError as e:
                print(f"GitLab project not found: {project_path}")
                return None
            
            try:
                mr = project.mergerequests.get(mr_number)
            except gitlab.exceptions.GitlabGetError as e:
                print(f"GitLab merge request not found: {mr_number}")
                return None
            
            # Get files changed
            files_changed = []
            try:
                changes = mr.changes()
                # GitLab returns changes as a list directly, not wrapped in a 'changes' key
                if isinstance(changes, list):
                    changes_list = changes
                elif isinstance(changes, dict) and 'changes' in changes:
                    changes_list = changes['changes']
                else:
                    changes_list = []
                
                for change in changes_list:
                    if isinstance(change, dict):
                        files_changed.append({
                            'filename': change.get('new_path', change.get('old_path', '')),
                            'status': self._get_file_status(change),
                            'additions': change.get('diff', '').count('\n+') - 1,  # Approximate
                            'deletions': change.get('diff', '').count('\n-') - 1,  # Approximate
                            'patch': change.get('diff', '')
                        })
            except Exception as e:
                print(f"Warning: Could not fetch file changes: {e}")
            
            # Create PullRequest object
            pull_request = PullRequest(
                id=str(mr.id),
                title=mr.title,
                description=mr.description or '',
                author=mr.author.get('username', '') if mr.author else '',
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                status='merged' if mr.state == 'merged' else ('closed' if mr.state == 'closed' else 'open'),
                created_at=self._parse_datetime(mr.created_at),
                updated_at=self._parse_datetime(mr.updated_at),
                platform='gitlab',
                repository_url=project.web_url,
                pr_url=mr.web_url,
                files_changed=files_changed,
                additions=mr.additions if hasattr(mr, 'additions') else 0,
                deletions=mr.deletions if hasattr(mr, 'deletions') else 0,
                commits_count=mr.commits_count if hasattr(mr, 'commits_count') else 0,
                labels=[label.get('name', '') for label in mr.labels] if mr.labels else [],
                assignees=[assignee.get('username', '') for assignee in mr.assignees] if mr.assignees else [],
                reviewers=[reviewer.get('username', '') for reviewer in mr.reviewers] if hasattr(mr, 'reviewers') and mr.reviewers else []
            )
            
            return pull_request
            
        except gitlab.exceptions.GitlabError as e:
            print(f"GitLab API error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching MR: {e}")
            return None
    
    def add_review_comment(self, repo_url: str, mr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> bool:
        """
        Add a review comment to a merge request
        
        Args:
            repo_url: GitLab repository URL
            mr_number: Merge request number
            comment: Comment text
            file_path: File path for inline comment (optional)
            line_number: Line number for inline comment (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            project_path = self._extract_project_path(repo_url)
            if not project_path:
                return False
            
            project = self.gitlab.projects.get(project_path)
            mr = project.mergerequests.get(mr_number)
            
            if file_path and line_number:
                # Add inline comment (note on specific line)
                mr.notes.create({
                    'body': comment,
                    'position': {
                        'base_sha': mr.diff_refs.get('base_sha'),
                        'head_sha': mr.diff_refs.get('head_sha'),
                        'start_sha': mr.diff_refs.get('start_sha'),
                        'new_path': file_path,
                        'new_line': line_number
                    }
                })
            else:
                # Add general comment
                mr.notes.create({'body': comment})
            
            return True
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def _extract_project_path(self, repo_url: str) -> Optional[str]:
        """Extract project path from GitLab URL"""
        if repo_url.startswith('https://gitlab.com/'):
            # Full URL: https://gitlab.com/owner/repo
            path_part = repo_url.replace('https://gitlab.com/', '')
            parts = path_part.split('/')
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        elif repo_url.startswith('https://') and 'gitlab' in repo_url:
            # Custom GitLab instance
            parts = repo_url.split('/')
            if len(parts) >= 5:  # https://gitlab.example.com/owner/repo
                return f"{parts[3]}/{parts[4]}"
        elif '/' in repo_url and not repo_url.startswith('http'):
            # Already in owner/repo format
            return repo_url
        
        return None
    
    def _get_file_status(self, change: dict) -> str:
        """Determine file status from GitLab change object"""
        if not isinstance(change, dict):
            return 'modified'
        
        if change.get('new_file'):
            return 'added'
        elif change.get('deleted_file'):
            return 'deleted'
        elif change.get('renamed_file'):
            return 'renamed'
        else:
            return 'modified'
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse GitLab datetime string"""
        if not datetime_str:
            return None
        try:
            # GitLab uses ISO format: 2023-01-01T12:00:00.000Z
            if isinstance(datetime_str, str):
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            elif hasattr(datetime_str, 'isoformat'):
                return datetime_str
            else:
                return None
        except Exception:
            return None
    
    def test_connection(self) -> bool:
        """Test GitLab API connection"""
        try:
            if self.access_token:
                user = self.gitlab.user
                print(f"Connected to GitLab as: {user.username}")
            else:
                # Test with a public project
                projects = self.gitlab.projects.list(per_page=1)
                print("Connected to GitLab (anonymous)")
            return True
        except Exception as e:
            print(f"GitLab connection failed: {e}")
            return False
