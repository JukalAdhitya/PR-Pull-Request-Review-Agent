from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class PullRequest:
    """Data model for pull request information across different Git platforms"""
    
    # Basic PR information
    id: str
    title: str
    description: str
    author: str
    source_branch: str
    target_branch: str
    status: str  # open, closed, merged
    created_at: datetime
    updated_at: datetime
    
    # Platform information
    platform: str  # github, gitlab, bitbucket
    repository_url: str
    pr_url: str
    
    # Code changes
    files_changed: List[Dict[str, str]]  # [{'filename': str, 'status': str, 'patch': str}]
    additions: int
    deletions: int
    commits_count: int
    
    # Optional metadata
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    reviewers: Optional[List[str]] = None
    
    def get_total_changes(self) -> int:
        """Get total number of lines changed"""
        return self.additions + self.deletions
    
    def get_changed_files_summary(self) -> Dict[str, int]:
        """Get summary of changed files by type"""
        summary = {}
        for file_info in self.files_changed:
            filename = file_info.get('filename', '')
            extension = filename.split('.')[-1] if '.' in filename else 'no_extension'
            summary[extension] = summary.get(extension, 0) + 1
        return summary
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'source_branch': self.source_branch,
            'target_branch': self.target_branch,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'platform': self.platform,
            'repository_url': self.repository_url,
            'pr_url': self.pr_url,
            'files_changed': self.files_changed,
            'additions': self.additions,
            'deletions': self.deletions,
            'commits_count': self.commits_count,
            'labels': self.labels,
            'assignees': self.assignees,
            'reviewers': self.reviewers,
            'total_changes': self.get_total_changes(),
            'changed_files_summary': self.get_changed_files_summary()
        }

