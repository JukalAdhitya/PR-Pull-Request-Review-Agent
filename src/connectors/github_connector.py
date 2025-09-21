import os
from typing import Optional, List
from datetime import datetime
from github import Github, GithubException
from src.models.pull_request import PullRequest

class GitHubConnector:
    """Connector for GitHub API using PyGithub"""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize GitHub connector with access token"""
        self.access_token = access_token or os.getenv('GITHUB_TOKEN')
        if self.access_token:
            self.github = Github(self.access_token)
        else:
            # Use unauthenticated access (limited rate)
            self.github = Github()
    
    def get_pull_request(self, repo_url: str, pr_number: int) -> Optional[PullRequest]:
        """
        Fetch pull request data from GitHub
        
        Args:
            repo_url: GitHub repository URL (e.g., 'owner/repo' or full URL)
            pr_number: Pull request number
            
        Returns:
            PullRequest object or None if not found
        """
        try:
            # Extract owner/repo from URL
            repo_path = self._extract_repo_path(repo_url)
            if not repo_path:
                raise ValueError(f"Invalid repository URL: {repo_url}")
            
            # Get repository and pull request
            repo = self.github.get_repo(repo_path)
            pr = repo.get_pull(pr_number)
            
            # Get files changed
            files_changed = []
            for file in pr.get_files():
                files_changed.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'patch': file.patch or ''
                })
            
            # Create PullRequest object
            pull_request = PullRequest(
                id=str(pr.id),
                title=pr.title,
                description=pr.body or '',
                author=pr.user.login,
                source_branch=pr.head.ref,
                target_branch=pr.base.ref,
                status='merged' if pr.merged else ('closed' if pr.state == 'closed' else 'open'),
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                platform='github',
                repository_url=repo.html_url,
                pr_url=pr.html_url,
                files_changed=files_changed,
                additions=pr.additions,
                deletions=pr.deletions,
                commits_count=pr.commits,
                labels=[label.name for label in pr.labels],
                assignees=[assignee.login for assignee in pr.assignees],
                reviewers=[reviewer.login for reviewer in pr.requested_reviewers]
            )
            
            return pull_request
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching PR: {e}")
            return None
    
    def add_review_comment(self, repo_url: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> bool:
        """
        Add a review comment to a pull request
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            comment: Comment text
            file_path: File path for inline comment (optional)
            line_number: Line number for inline comment (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            repo_path = self._extract_repo_path(repo_url)
            if not repo_path:
                return False
            
            repo = self.github.get_repo(repo_path)
            pr = repo.get_pull(pr_number)
            
            if file_path and line_number:
                # Add inline comment
                commit = pr.get_commits().reversed[0]  # Latest commit
                pr.create_review_comment(
                    body=comment,
                    commit=commit,
                    path=file_path,
                    line=line_number
                )
            else:
                # Add general comment
                pr.create_issue_comment(comment)
            
            return True
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def _extract_repo_path(self, repo_url: str) -> Optional[str]:
        """Extract owner/repo path from GitHub URL"""
        if repo_url.startswith('https://github.com/'):
            # Full URL: https://github.com/owner/repo
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        elif '/' in repo_url and not repo_url.startswith('http'):
            # Already in owner/repo format
            return repo_url
        
        return None
    
    def test_connection(self) -> bool:
        """Test GitHub API connection"""
        try:
            user = self.github.get_user()
            print(f"Connected to GitHub as: {user.login if self.access_token else 'Anonymous'}")
            return True
        except Exception as e:
            print(f"GitHub connection failed: {e}")
            return False

