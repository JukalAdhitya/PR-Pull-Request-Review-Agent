# PR Review Agent - User Guide

This guide provides detailed instructions on how to use the PR Review Agent for analyzing pull requests across different Git platforms.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Web Interface](#web-interface)
3. [API Usage](#api-usage)
4. [Understanding Results](#understanding-results)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before using the PR Review Agent, ensure you have:

- Python 3.8 or higher installed
- A Hugging Face API token for AI-powered analysis
- Git platform access tokens (for private repositories)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pr-review-agent.git
   cd pr-review-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   export HF_TOKEN="your-huggingface-token"
   export GITHUB_TOKEN="your-github-token"  # Optional, for private repos
   ```

5. Start the application:
   ```bash
   python src/main.py
   ```

6. Access the web interface at `http://localhost:5000`

## Web Interface

The PR Review Agent provides a user-friendly web interface for analyzing pull requests.

### Analyzing a Pull Request

1. Open your browser and navigate to `http://localhost:5000`
2. Fill in the form with the following information:
   - **Git Platform**: Select GitHub, GitLab, or Bitbucket
   - **Repository URL**: Enter the repository URL or owner/repo format
   - **Pull Request Number**: Enter the PR number to analyze
   - **GitHub Token** (Optional): Provide a token for private repositories
3. Click "Analyze Pull Request" to start the analysis
4. Wait for the analysis to complete (this may take a few moments)

### Demo Mode

If you want to see how the analysis works without providing a real PR:

1. Click the "Try Demo Analysis" button
2. The system will analyze a sample PR and display the results

## API Usage

The PR Review Agent provides a RESTful API for integration with other tools and services.

### Authentication

No authentication is required for the API in the current version. For production use, consider adding API key authentication.

### Endpoints

#### Analyze Pull Request

```
POST /api/review/analyze
```

Request body:
```json
{
  "platform": "github",
  "repo_url": "owner/repo",
  "pr_number": 123,
  "github_token": "optional-token"
}
```

Response:
```json
{
  "success": true,
  "pr_info": {
    "title": "Example PR",
    "author": "username",
    "platform": "github",
    "status": "open",
    "files_changed": 5,
    "additions": 120,
    "deletions": 50
  },
  "review_result": {
    "quality_score": {
      "overall_score": 85.5,
      "grade": "B",
      "readability_score": 88.0,
      "performance_score": 82.0,
      "security_score": 90.0,
      "maintainability_score": 85.0,
      "best_practices_score": 83.0
    },
    "feedback_items": [
      {
        "type": "readability",
        "severity": "medium",
        "message": "Variable names are not descriptive",
        "file_path": "src/main.js",
        "line_number": 42,
        "suggestion": "Use more descriptive variable names"
      }
    ],
    "recommendations": [
      "Review and fix high-priority issues",
      "Consider additional code review from team members"
    ]
  }
}
```

#### Health Check

```
GET /api/review/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "github_connector": "available",
    "ai_analyzer": "available",
    "github_api": "connected"
  }
}
```

#### Supported Platforms

```
GET /api/review/platforms
```

Response:
```json
{
  "supported_platforms": [
    {
      "name": "github",
      "display_name": "GitHub",
      "status": "fully_supported",
      "features": ["fetch_pr_data", "ai_analysis", "inline_comments", "quality_scoring"]
    },
    {
      "name": "gitlab",
      "display_name": "GitLab",
      "status": "planned",
      "features": []
    },
    {
      "name": "bitbucket",
      "display_name": "Bitbucket",
      "status": "planned",
      "features": []
    }
  ]
}
```

### API Examples

#### cURL

```bash
curl -X POST http://localhost:5000/api/review/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "github",
    "repo_url": "owner/repo",
    "pr_number": 123
  }'
```

#### Python

```python
import requests

url = "http://localhost:5000/api/review/analyze"
data = {
    "platform": "github",
    "repo_url": "owner/repo",
    "pr_number": 123,
    "github_token": "your-github-token"  # Optional
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

## Understanding Results

The PR Review Agent provides comprehensive analysis results:

### Quality Score

The quality score is a numerical assessment of the code quality in the PR:

- **Overall Score**: A score from 0-100 representing the overall code quality
- **Grade**: A letter grade (A, B, C, D, F) based on the overall score
- **Category Scores**: Individual scores for readability, performance, security, maintainability, and best practices

### Feedback Items

Feedback items are specific issues identified in the code:

- **Type**: The category of the issue (readability, performance, security, etc.)
- **Severity**: How critical the issue is (low, medium, high, critical)
- **Message**: A description of the issue
- **File Path**: The file where the issue was found
- **Line Number**: The specific line number (if available)
- **Suggestion**: A recommended fix for the issue
- **Code Snippet**: The relevant code (if available)

### Recommendations

Recommendations are actionable suggestions based on the analysis:

- **High-Priority Issues**: Focus on critical and high-severity issues first
- **Code Quality Improvements**: Suggestions for improving overall code quality
- **Best Practices**: Recommendations for following industry best practices

## CI/CD Integration

The PR Review Agent can be integrated into CI/CD pipelines for automated code reviews.

### GitHub Actions Example

```yaml
name: PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: PR Review
        uses: curl
        with:
          args: -X POST https://your-pr-review-agent-url/api/review/analyze -H "Content-Type: application/json" -d '{"platform": "github", "repo_url": "${{ github.repository }}", "pr_number": ${{ github.event.pull_request.number }}, "github_token": "${{ secrets.GITHUB_TOKEN }}"}'
```

### GitLab CI Example

```yaml
pr_review:
  stage: test
  script:
    - curl -X POST https://your-pr-review-agent-url/api/review/analyze -H "Content-Type: application/json" -d '{"platform": "gitlab", "repo_url": "$CI_PROJECT_PATH", "pr_number": $CI_MERGE_REQUEST_IID, "github_token": "$GITLAB_TOKEN"}'
  only:
    - merge_requests
```

## Troubleshooting

### Common Issues

#### API Key Issues

If you encounter errors related to the OpenAI API key:

1. Ensure the `OPENAI_API_KEY` environment variable is set correctly
2. Verify that your API key is valid and has sufficient credits
3. Check the API key permissions and rate limits

#### Connection Issues

If the agent cannot connect to Git platforms:

1. Check your internet connection
2. Verify that the repository URL is correct
3. Ensure your access token has the necessary permissions
4. Check if the Git platform's API is operational

#### Analysis Failures

If the analysis fails:

1. Check if the PR exists and is accessible
2. Verify that the PR contains valid code changes
3. Check the server logs for specific error messages
4. Try analyzing a different PR to see if the issue persists

### Getting Help

If you encounter issues not covered in this guide:

1. Check the GitHub repository for known issues
2. Open a new issue with detailed information about the problem
3. Include error messages, logs, and steps to reproduce the issue

