from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class FeedbackType(Enum):
    """Types of feedback that can be provided"""
    READABILITY = "readability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"
    BUG_RISK = "bug_risk"
    MAINTAINABILITY = "maintainability"

class Severity(Enum):
    """Severity levels for feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Feedback:
    """Individual feedback item"""
    type: FeedbackType
    severity: Severity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class QualityScore:
    """Quality scoring breakdown"""
    overall_score: float  # 0-100
    readability_score: float
    performance_score: float
    security_score: float
    maintainability_score: float
    best_practices_score: float
    
    def get_grade(self) -> str:
        """Convert overall score to letter grade"""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"

@dataclass
class ReviewResult:
    """Complete review result for a pull request"""
    
    # Basic information
    pr_id: str
    review_id: str
    timestamp: datetime
    
    # Analysis results
    feedback_items: List[Feedback]
    quality_score: QualityScore
    
    # Summary
    summary: str
    recommendations: List[str]
    
    # Metrics
    total_issues: int = field(init=False)
    critical_issues: int = field(init=False)
    high_issues: int = field(init=False)
    medium_issues: int = field(init=False)
    low_issues: int = field(init=False)
    
    def __post_init__(self):
        """Calculate metrics after initialization"""
        self.total_issues = len(self.feedback_items)
        self.critical_issues = len([f for f in self.feedback_items if f.severity == Severity.CRITICAL])
        self.high_issues = len([f for f in self.feedback_items if f.severity == Severity.HIGH])
        self.medium_issues = len([f for f in self.feedback_items if f.severity == Severity.MEDIUM])
        self.low_issues = len([f for f in self.feedback_items if f.severity == Severity.LOW])
    
    def get_feedback_by_type(self, feedback_type: FeedbackType) -> List[Feedback]:
        """Get all feedback items of a specific type"""
        return [f for f in self.feedback_items if f.type == feedback_type]
    
    def get_feedback_by_severity(self, severity: Severity) -> List[Feedback]:
        """Get all feedback items of a specific severity"""
        return [f for f in self.feedback_items if f.severity == severity]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'pr_id': self.pr_id,
            'review_id': self.review_id,
            'timestamp': self.timestamp.isoformat(),
            'feedback_items': [
                {
                    'type': f.type.value,
                    'severity': f.severity.value,
                    'message': f.message,
                    'file_path': f.file_path,
                    'line_number': f.line_number,
                    'suggestion': f.suggestion,
                    'code_snippet': f.code_snippet
                } for f in self.feedback_items
            ],
            'quality_score': {
                'overall_score': self.quality_score.overall_score,
                'readability_score': self.quality_score.readability_score,
                'performance_score': self.quality_score.performance_score,
                'security_score': self.quality_score.security_score,
                'maintainability_score': self.quality_score.maintainability_score,
                'best_practices_score': self.quality_score.best_practices_score,
                'grade': self.quality_score.get_grade()
            },
            'summary': self.summary,
            'recommendations': self.recommendations,
            'metrics': {
                'total_issues': self.total_issues,
                'critical_issues': self.critical_issues,
                'high_issues': self.high_issues,
                'medium_issues': self.medium_issues,
                'low_issues': self.low_issues
            }
        }

