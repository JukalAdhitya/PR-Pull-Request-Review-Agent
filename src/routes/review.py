from flask import Blueprint, request, jsonify
from typing import Dict, Any
import traceback

from src.connectors.github_connector import GitHubConnector
from src.connectors.gitlab_connector import GitLabConnector
from src.connectors.bitbucket_connector import BitbucketConnector
from src.analyzers.ai_analyzer import AIAnalyzer

review_bp = Blueprint('review', __name__)

# Initialize connectors and analyzers
github_connector = GitHubConnector()
gitlab_connector = GitLabConnector()
bitbucket_connector = BitbucketConnector()
ai_analyzer = None

def get_ai_analyzer():
    """Get AI analyzer instance (lazy initialization)"""
    global ai_analyzer
    if ai_analyzer is None:
        try:
            ai_analyzer = AIAnalyzer()
        except ValueError as e:
            print(f"Warning: AI analyzer not available: {e}")
            ai_analyzer = None
    return ai_analyzer

@review_bp.route('/analyze', methods=['POST'])
def analyze_pull_request():
    """
    Analyze a pull request and return AI-generated feedback
    
    Expected JSON payload:
    {
        "platform": "github|gitlab|bitbucket",
        "repo_url": "owner/repo or full URL",
        "pr_number": 123,
        "access_token": "optional_token",
        "gitlab_url": "optional_gitlab_instance_url",
        "bitbucket_username": "optional_bitbucket_username",
        "bitbucket_app_password": "optional_bitbucket_app_password"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        platform = data.get('platform', '').lower()
        repo_url = data.get('repo_url', '').strip()
        pr_number = data.get('pr_number')
        
        if not all([platform, repo_url, pr_number]):
            return jsonify({
                "error": "Missing required fields: platform, repo_url, pr_number"
            }), 400
        
        if platform not in ['github', 'gitlab', 'bitbucket']:
            return jsonify({
                "error": f"Unsupported platform: {platform}",
                "supported_platforms": ["github", "gitlab", "bitbucket"]
            }), 400
        
        try:
            pr_number = int(pr_number)
        except (ValueError, TypeError):
            return jsonify({"error": "pr_number must be a valid integer"}), 400
        
        # Initialize connector based on platform
        connector = None
        if platform == 'github':
            github_token = data.get('access_token') or data.get('github_token')
            if github_token:
                connector = GitHubConnector(github_token)
            else:
                connector = github_connector
        elif platform == 'gitlab':
            gitlab_token = data.get('access_token') or data.get('gitlab_token')
            gitlab_url = data.get('gitlab_url', 'https://gitlab.com')
            if gitlab_token:
                connector = GitLabConnector(gitlab_token, gitlab_url)
            else:
                connector = GitLabConnector(gitlab_url=gitlab_url)
        elif platform == 'bitbucket':
            bitbucket_username = data.get('bitbucket_username')
            bitbucket_app_password = data.get('bitbucket_app_password')
            if bitbucket_username and bitbucket_app_password:
                connector = BitbucketConnector(bitbucket_username, bitbucket_app_password)
            else:
                connector = bitbucket_connector
        
        # Fetch pull request data
        pr = connector.get_pull_request(repo_url, pr_number)
        if not pr:
            return jsonify({
                "error": f"Could not fetch PR #{pr_number} from {repo_url}",
                "details": "Check if the repository exists and PR number is correct"
            }), 404
        
        # Analyze with AI
        analyzer = get_ai_analyzer()
        if not analyzer:
            return jsonify({
                "error": "AI analysis not available",
                "details": "OpenAI API key not configured"
            }), 503
        
        review_result = analyzer.analyze_pull_request(pr)
        
        # Return comprehensive result
        return jsonify({
            "success": True,
            "pr_info": pr.to_dict(),
            "review_result": review_result.to_dict(),
            "analysis_timestamp": review_result.timestamp.isoformat()
        })
        
    except Exception as e:
        print(f"Error in analyze_pull_request: {e}")
        print(traceback.format_exc())
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@review_bp.route('/platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported Git platforms"""
    return jsonify({
        "supported_platforms": [
            {
                "name": "github",
                "display_name": "GitHub",
                "status": "fully_supported",
                "features": [
                    "fetch_pr_data",
                    "ai_analysis",
                    "inline_comments",
                    "quality_scoring"
                ],
                "auth_required": False,
                "auth_type": "personal_access_token"
            },
            {
                "name": "gitlab",
                "display_name": "GitLab",
                "status": "fully_supported",
                "features": [
                    "fetch_pr_data",
                    "ai_analysis",
                    "inline_comments",
                    "quality_scoring"
                ],
                "auth_required": False,
                "auth_type": "personal_access_token",
                "supports_custom_instance": True
            },
            {
                "name": "bitbucket",
                "display_name": "Bitbucket",
                "status": "fully_supported",
                "features": [
                    "fetch_pr_data",
                    "ai_analysis",
                    "inline_comments",
                    "quality_scoring"
                ],
                "auth_required": False,
                "auth_type": "app_password"
            }
        ]
    })

@review_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "services": {
            "github_connector": "available",
            "gitlab_connector": "available",
            "bitbucket_connector": "available",
            "ai_analyzer": "available" if get_ai_analyzer() else "unavailable"
        }
    }
    
    # Test GitHub connection
    try:
        if github_connector.test_connection():
            status["services"]["github_api"] = "connected"
        else:
            status["services"]["github_api"] = "connection_failed"
    except Exception:
        status["services"]["github_api"] = "error"
    
    # Test GitLab connection
    try:
        if gitlab_connector.test_connection():
            status["services"]["gitlab_api"] = "connected"
        else:
            status["services"]["gitlab_api"] = "connection_failed"
    except Exception:
        status["services"]["gitlab_api"] = "error"
    
    # Test Bitbucket connection
    try:
        if bitbucket_connector.test_connection():
            status["services"]["bitbucket_api"] = "connected"
        else:
            status["services"]["bitbucket_api"] = "connection_failed"
    except Exception:
        status["services"]["bitbucket_api"] = "error"
    
    return jsonify(status)

@review_bp.route('/demo', methods=['GET'])
def demo_analysis():
    """
    Demo endpoint with a sample PR analysis
    Uses a well-known public repository for demonstration
    """
    try:
        # Use a popular public repository for demo
        demo_repo = "microsoft/vscode"
        
        # Get a recent merged PR (you might want to update this periodically)
        demo_pr_number = 200000  # This might need to be updated to a valid PR
        
        # Try to fetch the PR
        pr = github_connector.get_pull_request(demo_repo, demo_pr_number)
        
        if not pr:
            # Fallback demo data
            return jsonify({
                "demo": True,
                "message": "Demo analysis with sample data",
                "sample_analysis": {
                    "pr_info": {
                        "title": "Sample Pull Request",
                        "description": "This is a demo analysis",
                        "platform": "github",
                        "files_changed": 3,
                        "additions": 45,
                        "deletions": 12
                    },
                    "quality_score": {
                        "overall_score": 85.5,
                        "grade": "B",
                        "readability_score": 88.0,
                        "performance_score": 82.0,
                        "security_score": 90.0,
                        "maintainability_score": 85.0,
                        "best_practices_score": 83.0
                    },
                    "feedback_summary": {
                        "total_issues": 4,
                        "critical_issues": 0,
                        "high_issues": 1,
                        "medium_issues": 2,
                        "low_issues": 1
                    },
                    "recommendations": [
                        "Review and fix high-priority issues",
                        "Consider additional code review from team members"
                    ]
                }
            })
        
        # Analyze the real PR
        analyzer = get_ai_analyzer()
        if analyzer:
            review_result = analyzer.analyze_pull_request(pr)
            return jsonify({
                "demo": True,
                "pr_info": pr.to_dict(),
                "review_result": review_result.to_dict()
            })
        else:
            return jsonify({
                "demo": True,
                "error": "AI analysis not available for demo"
            })
            
    except Exception as e:
        return jsonify({
            "demo": True,
            "error": f"Demo failed: {str(e)}"
        }), 500

