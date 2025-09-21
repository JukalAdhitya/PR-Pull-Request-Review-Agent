#!/usr/bin/env python3
"""
Simple test script for PR Review Agent
Tests basic functionality without requiring external APIs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.models.pull_request import PullRequest
from src.models.review_result import ReviewResult, Feedback, QualityScore, FeedbackType, Severity
from src.connectors.github_connector import GitHubConnector
from datetime import datetime

def test_models():
    """Test data models"""
    print("Testing data models...")
    
    # Test PullRequest model
    pr = PullRequest(
        id="123",
        title="Test PR",
        description="Test description",
        author="testuser",
        source_branch="feature/test",
        target_branch="main",
        status="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        platform="github",
        repository_url="https://github.com/test/repo",
        pr_url="https://github.com/test/repo/pull/123",
        files_changed=[{"filename": "test.py", "status": "modified", "patch": "test patch"}],
        additions=10,
        deletions=5,
        commits_count=3
    )
    
    print(f"✓ PullRequest model created: {pr.title}")
    print(f"✓ Total changes: {pr.get_total_changes()}")
    print(f"✓ File summary: {pr.get_changed_files_summary()}")
    
    # Test ReviewResult model
    feedback = Feedback(
        type=FeedbackType.READABILITY,
        severity=Severity.MEDIUM,
        message="Test feedback message",
        suggestion="Test suggestion"
    )
    
    quality_score = QualityScore(
        overall_score=85.0,
        readability_score=80.0,
        performance_score=90.0,
        security_score=85.0,
        maintainability_score=80.0,
        best_practices_score=90.0
    )
    
    review_result = ReviewResult(
        pr_id="123",
        review_id="review_123",
        timestamp=datetime.now(),
        feedback_items=[feedback],
        quality_score=quality_score,
        summary="Test review summary",
        recommendations=["Test recommendation"]
    )
    
    print(f"✓ ReviewResult model created with grade: {quality_score.get_grade()}")
    print(f"✓ Total issues: {review_result.total_issues}")
    
    return True

def test_github_connector():
    """Test GitHub connector (without API calls)"""
    print("\nTesting GitHub connector...")
    
    connector = GitHubConnector()
    
    # Test URL parsing
    test_urls = [
        "https://github.com/owner/repo",
        "owner/repo",
        "invalid-url"
    ]
    
    for url in test_urls:
        result = connector._extract_repo_path(url)
        print(f"✓ URL '{url}' -> '{result}'")
    
    return True

def test_flask_routes():
    """Test Flask routes (basic import test)"""
    print("\nTesting Flask routes...")
    
    try:
        from src.routes.review import review_bp
        print("✓ Review routes imported successfully")
        
        from src.main import app
        print("✓ Flask app created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Flask routes test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== PR Review Agent Test Suite ===\n")
    
    tests = [
        test_models,
        test_github_connector,
        test_flask_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ PASSED\n")
            else:
                print("✗ FAILED\n")
        except Exception as e:
            print(f"✗ FAILED: {e}\n")
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

