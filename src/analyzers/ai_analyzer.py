import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from huggingface_hub import InferenceClient

from src.models.pull_request import PullRequest
from src.models.review_result import ReviewResult, Feedback, QualityScore, FeedbackType, Severity

class AIAnalyzer:
    """AI-powered code analyzer using Hugging Face StarCoder2 model"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI analyzer with Hugging Face API key"""
        self.api_key = api_key or os.getenv("HF_TOKEN")
        if not self.api_key:
            raise ValueError("Hugging Face API token is required")
        
        self.client = InferenceClient(
            api_key=self.api_key,
        )
        self.model = "mistralai/Mistral-7B-Instruct-v0.2"
    
    def analyze_pull_request(self, pr: PullRequest) -> ReviewResult:
        """
        Analyze a pull request and generate comprehensive feedback
        
        Args:
            pr: PullRequest object to analyze
            
        Returns:
            ReviewResult with AI-generated feedback and scoring
        """
        try:
            # Prepare code changes for analysis
            code_changes = self._prepare_code_changes(pr)
            
            # Generate AI feedback
            feedback_items = self._generate_feedback(pr, code_changes)
            
            # Calculate quality scores
            quality_score = self._calculate_quality_scores(feedback_items, pr)
            
            # Generate summary and recommendations
            summary = self._generate_summary(pr, feedback_items, quality_score)
            recommendations = self._generate_recommendations(feedback_items, quality_score)
            
            # Create review result
            review_result = ReviewResult(
                pr_id=pr.id,
                review_id=f"review_{pr.id}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                feedback_items=feedback_items,
                quality_score=quality_score,
                summary=summary,
                recommendations=recommendations
            )
            
            return review_result
            
        except Exception as e:
            print(f"Error analyzing PR: {e}")
            # Return basic result with error
            return ReviewResult(
                pr_id=pr.id,
                review_id=f"error_{pr.id}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                feedback_items=[],
                quality_score=QualityScore(50.0, 50.0, 50.0, 50.0, 50.0, 50.0),
                summary=f"Analysis failed: {str(e)}",
                recommendations=["Please check the code manually"]
            )
    
    def _prepare_code_changes(self, pr: PullRequest) -> str:
        """Prepare code changes for AI analysis"""
        changes_text = f"Pull Request: {pr.title}\n"
        changes_text += f"Description: {pr.description}\n"
        changes_text += f"Files changed: {len(pr.files_changed)}\n"
        changes_text += f"Additions: {pr.additions}, Deletions: {pr.deletions}\n\n"
        
        for file_info in pr.files_changed[:10]:  # Limit to first 10 files
            changes_text += f"File: {file_info['filename']}\n"
            changes_text += f"Status: {file_info['status']}\n"
            if file_info.get("patch"):
                changes_text += f"Changes:\n{file_info['patch']}\n"
            changes_text += "\n---\n\n"
        
        return changes_text
    
    def _generate_feedback(self, pr: PullRequest, code_changes: str) -> List[Feedback]:
        """Generate AI feedback for code changes using StarCoder2 model"""
        try:
            prompt = f"""You are StarCoder2, an expert code reviewer and software engineer. Analyze the following pull request and provide comprehensive code review feedback.

Focus on these key areas:
- Code quality and readability
- Performance optimization opportunities  
- Security vulnerabilities and best practices
- Potential bugs and logic issues
- Maintainability and code structure
- Adherence to coding standards and best practices

Pull Request Details:
{code_changes}

Please provide your analysis in the following JSON format:
{{
    "feedback": [
        {{
            "type": "readability|performance|security|best_practices|bug_risk|maintainability",
            "severity": "low|medium|high|critical",
            "message": "Detailed explanation of the issue or observation",
            "file_path": "path/to/file.py",
            "line_number": 42,
            "suggestion": "Specific actionable improvement suggestion",
            "code_snippet": "relevant code snippet if applicable"
        }}
    ]
}}

IMPORTANT: Use ONLY these exact type values: readability, performance, security, best_practices, bug_risk, maintainability
IMPORTANT: Use ONLY these exact severity values: low, medium, high, critical

Provide 3-7 high-quality feedback items covering different aspects of code quality. Be specific and actionable in your recommendations."""

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse AI response
            ai_response = completion.choices[0].message.content
            feedback_data = self._parse_ai_response(ai_response)
            
            # Convert to Feedback objects
            feedback_items = []
            for item in feedback_data.get("feedback", []):
                try:
                    # Handle unknown feedback types by mapping them to known ones
                    feedback_type = item.get("type", "best_practices")
                    if feedback_type not in [ft.value for ft in FeedbackType]:
                        # Map unknown types to closest known type
                        type_mapping = {
                            "code_structure": "maintainability",
                            "documentation": "readability", 
                            "testing": "best_practices",
                            "style": "readability",
                            "formatting": "readability",
                            "naming": "readability",
                            "complexity": "maintainability"
                        }
                        feedback_type = type_mapping.get(feedback_type, "best_practices")
                    
                    # Handle unknown severity levels
                    severity = item.get("severity", "medium")
                    if severity not in [s.value for s in Severity]:
                        severity = "medium"
                    
                    feedback = Feedback(
                        type=FeedbackType(feedback_type),
                        severity=Severity(severity),
                        message=item.get("message", "No message provided"),
                        file_path=item.get("file_path"),
                        line_number=item.get("line_number"),
                        suggestion=item.get("suggestion"),
                        code_snippet=item.get("code_snippet")
                    )
                    feedback_items.append(feedback)
                except (ValueError, KeyError) as e:
                    print(f"Error parsing feedback item: {e}")
                    print(f"Item data: {item}")
                    continue
            
            # Add some default feedback if AI didn't provide enough
            if len(feedback_items) < 3:
                feedback_items.extend(self._generate_default_feedback(pr))
            
            return feedback_items
            
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return self._generate_default_feedback(pr)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response and extract JSON"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback: create structured response from text
                return {"feedback": []}
        except json.JSONDecodeError:
            return {"feedback": []}
    
    def _generate_default_feedback(self, pr: PullRequest) -> List[Feedback]:
        """Generate default feedback when AI analysis fails"""
        feedback_items = []
        
        # Check PR size
        if pr.get_total_changes() > 500:
            feedback_items.append(Feedback(
                type=FeedbackType.BEST_PRACTICES,
                severity=Severity.MEDIUM,
                message="Large pull request detected. Consider breaking it into smaller, focused changes.",
                suggestion="Split this PR into multiple smaller PRs, each addressing a single concern."
            ))
        
        # Check file types
        file_summary = pr.get_changed_files_summary()
        if len(file_summary) > 5:
            feedback_items.append(Feedback(
                type=FeedbackType.MAINTAINABILITY,
                severity=Severity.LOW,
                message="Multiple file types modified. Ensure changes are cohesive.",
                suggestion="Group related changes and consider separate PRs for different concerns."
            ))
        
        # Check commit count
        if pr.commits_count > 10:
            feedback_items.append(Feedback(
                type=FeedbackType.BEST_PRACTICES,
                severity=Severity.LOW,
                message="High number of commits. Consider squashing related commits.",
                suggestion="Use interactive rebase to squash related commits into logical units."
            ))
        
        # Add basic readability feedback
        feedback_items.append(Feedback(
            type=FeedbackType.READABILITY,
            severity=Severity.LOW,
            message="Code review completed with basic analysis.",
            suggestion="Consider adding more descriptive comments and documentation."
        ))
        
        return feedback_items
    
    def _calculate_quality_scores(self, feedback_items: List[Feedback], pr: PullRequest) -> QualityScore:
        """Calculate quality scores based on feedback and PR metrics"""
        # Base scores
        base_score = 85.0
        
        # Deduct points based on feedback severity
        severity_penalties = {
            Severity.LOW: 2,
            Severity.MEDIUM: 5,
            Severity.HIGH: 10,
            Severity.CRITICAL: 20
        }
        
        # Calculate category scores
        category_scores = {
            FeedbackType.READABILITY: base_score,
            FeedbackType.PERFORMANCE: base_score,
            FeedbackType.SECURITY: base_score,
            FeedbackType.MAINTAINABILITY: base_score,
            FeedbackType.BEST_PRACTICES: base_score
        }
        
        # Apply penalties
        for feedback in feedback_items:
            penalty = severity_penalties.get(feedback.severity, 5)
            if feedback.type in category_scores:
                category_scores[feedback.type] -= penalty
        
        # Ensure scores don't go below 0
        for category in category_scores:
            category_scores[category] = max(0, category_scores[category])
        
        # Calculate overall score
        overall_score = sum(category_scores.values()) / len(category_scores)
        
        # Apply PR size penalty
        if pr.get_total_changes() > 1000:
            overall_score -= 10
        elif pr.get_total_changes() > 500:
            overall_score -= 5
        
        overall_score = max(0, overall_score)
        
        return QualityScore(
            overall_score=overall_score,
            readability_score=category_scores[FeedbackType.READABILITY],
            performance_score=category_scores[FeedbackType.PERFORMANCE],
            security_score=category_scores[FeedbackType.SECURITY],
            maintainability_score=category_scores[FeedbackType.MAINTAINABILITY],
            best_practices_score=category_scores[FeedbackType.BEST_PRACTICES]
        )
    
    def _generate_summary(self, pr: PullRequest, feedback_items: List[Feedback], quality_score: QualityScore) -> str:
        """Generate summary of the review"""
        summary = f"Analyzed pull request '{pr.title}' with {len(pr.files_changed)} files changed "
        summary += f"({pr.additions} additions, {pr.deletions} deletions). "
        summary += f"Overall quality score: {quality_score.overall_score:.1f}/100 (Grade: {quality_score.get_grade()}). "
        
        if quality_score.overall_score >= 80:
            summary += "Good code quality with minor improvements needed."
        elif quality_score.overall_score >= 60:
            summary += "Moderate code quality with several areas for improvement."
        else:
            summary += "Code quality needs significant improvement before merging."
        
        return summary
    
    def _generate_recommendations(self, feedback_items: List[Feedback], quality_score: QualityScore) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Critical issues first
        critical_items = [f for f in feedback_items if f.severity == Severity.CRITICAL]
        if critical_items:
            recommendations.append("Address all critical issues before merging")
        
        # High priority issues
        high_items = [f for f in feedback_items if f.severity == Severity.HIGH]
        if high_items:
            recommendations.append("Review and fix high-priority issues")
        
        # Category-specific recommendations
        if quality_score.security_score < 70:
            recommendations.append("Conduct thorough security review")
        
        if quality_score.performance_score < 70:
            recommendations.append("Optimize performance-critical sections")
        
        if quality_score.readability_score < 70:
            recommendations.append("Improve code readability and documentation")
        
        # General recommendations
        if quality_score.overall_score < 80:
            recommendations.append("Consider additional code review from team members")
        
        if not recommendations:
            recommendations.append("Code looks good! Consider minor suggestions if any.")
        
        return recommendations

