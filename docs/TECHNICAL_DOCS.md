# PR Review Agent - Technical Documentation

This document provides technical details about the PR Review Agent's architecture, implementation, and design decisions.

## Architecture Overview

The PR Review Agent follows a modular architecture designed for extensibility and maintainability:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Web Interface  │     │   API Endpoints  │     │    CLI Tool     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Core Services  │
                        └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
│  Git Connectors  │     │  AI Analyzers   │     │  Data Models    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Components

1. **User Interfaces**:
   - Web Interface: Browser-based UI for human interaction
   - API Endpoints: RESTful API for programmatic access
   - CLI Tool: Command-line interface for scripting

2. **Core Services**:
   - Request handling and routing
   - Authentication and authorization
   - Error handling and logging

3. **Git Connectors**:
   - GitHub Connector: Interacts with GitHub API
   - GitLab Connector: Interacts with GitLab API
   - Bitbucket Connector: Interacts with Bitbucket API

4. **AI Analyzers**:
   - Code Analysis: Analyzes code changes for issues
   - Feedback Generation: Creates structured feedback
   - Scoring Engine: Calculates quality scores

5. **Data Models**:
   - PullRequest: Represents PR data from any platform
   - ReviewResult: Contains analysis results and feedback
   - QualityScore: Numerical scoring with breakdown

## Implementation Details

### Technology Stack

- **Backend**: Python 3.11, Flask
- **AI/ML**: OpenAI GPT-4 API
- **Git Integration**: PyGithub, python-gitlab, requests
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap)
- **Database**: SQLite (for demo purposes)

### Code Organization

The codebase is organized into the following directories:

- **src/**: Main source code
  - **models/**: Data models and database schemas
  - **connectors/**: Git platform API connectors
  - **analyzers/**: AI analysis and scoring engines
  - **routes/**: API endpoints and request handlers
  - **static/**: Frontend assets (HTML, CSS, JS)
  - **main.py**: Application entry point

- **tests/**: Test cases and test utilities
- **docs/**: Documentation files

### Data Flow

1. **Pull Request Analysis Flow**:
   ```
   User Request → API Endpoint → Git Connector → Fetch PR Data →
   AI Analyzer → Generate Feedback → Calculate Scores → Return Results
   ```

2. **Inline Comment Flow**:
   ```
   Review Result → Extract Feedback → Format Comments →
   Git Connector → Post Comments to PR
   ```

### Key Classes and Functions

#### PullRequest Model

```python
@dataclass
class PullRequest:
    id: str
    title: str
    description: str
    author: str
    source_branch: str
    target_branch: str
    status: str
    created_at: datetime
    updated_at: datetime
    platform: str
    repository_url: str
    pr_url: str
    files_changed: List[Dict[str, str]]
    additions: int
    deletions: int
    commits_count: int
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    reviewers: Optional[List[str]] = None
    
    # Methods for data processing and conversion
```

#### ReviewResult Model

```python
@dataclass
class ReviewResult:
    pr_id: str
    review_id: str
    timestamp: datetime
    feedback_items: List[Feedback]
    quality_score: QualityScore
    summary: str
    recommendations: List[str]
    
    # Metrics calculated after initialization
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    
    # Methods for filtering and conversion
```

#### GitHub Connector

```python
class GitHubConnector:
    def __init__(self, access_token: Optional[str] = None):
        # Initialize GitHub API client
    
    def get_pull_request(self, repo_url: str, pr_number: int) -> Optional[PullRequest]:
        # Fetch PR data from GitHub API
    
    def add_review_comment(self, repo_url: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> bool:
        # Add review comment to PR
```

#### AI Analyzer

```python
class AIAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        # Initialize OpenAI client
    
    def analyze_pull_request(self, pr: PullRequest) -> ReviewResult:
        # Analyze PR and generate feedback
    
    def _generate_feedback(self, pr: PullRequest, code_changes: str) -> List[Feedback]:
        # Generate AI feedback for code changes
    
    def _calculate_quality_scores(self, feedback_items: List[Feedback], pr: PullRequest) -> QualityScore:
        # Calculate quality scores based on feedback
```

## API Reference

### Endpoints

#### `POST /api/review/analyze`

Analyzes a pull request and returns feedback.

**Request Body**:
```json
{
  "platform": "github",
  "repo_url": "owner/repo",
  "pr_number": 123,
  "github_token": "optional-token"
}
```

**Response**:
```json
{
  "success": true,
  "pr_info": { ... },
  "review_result": { ... }
}
```

#### `GET /api/review/health`

Returns the health status of the service.

**Response**:
```json
{
  "status": "healthy",
  "services": { ... }
}
```

#### `GET /api/review/platforms`

Returns the list of supported Git platforms.

**Response**:
```json
{
  "supported_platforms": [ ... ]
}
```

#### `GET /api/review/demo`

Returns a demo analysis result.

**Response**:
```json
{
  "demo": true,
  "pr_info": { ... },
  "review_result": { ... }
}
```

## AI Analysis Details

### OpenAI Integration

The PR Review Agent uses OpenAI's GPT-4 model to analyze code changes and provide feedback. The integration works as follows:

1. **Prompt Construction**:
   - The code changes are formatted into a structured prompt
   - The prompt includes instructions for analyzing readability, performance, security, etc.
   - The model is asked to return feedback in a specific JSON format

2. **Response Parsing**:
   - The JSON response is parsed to extract feedback items
   - Each feedback item is converted to a `Feedback` object
   - If parsing fails, default feedback is generated based on PR metrics

3. **Quality Scoring**:
   - Quality scores are calculated based on feedback severity
   - Different categories (readability, performance, etc.) are scored separately
   - The overall score is a weighted average of category scores

### Prompt Engineering

The prompt used for AI analysis is carefully designed to elicit useful feedback:

```
You are an expert code reviewer. Analyze the following pull request and provide detailed feedback.
Focus on: readability, performance, security, best practices, potential bugs, and maintainability.

Pull Request Information:
{code_changes}

Please provide feedback in the following JSON format:
{
    "feedback": [
        {
            "type": "readability|performance|security|best_practices|bug_risk|maintainability",
            "severity": "low|medium|high|critical",
            "message": "Detailed feedback message",
            "file_path": "path/to/file.py",
            "line_number": 42,
            "suggestion": "Specific improvement suggestion",
            "code_snippet": "relevant code snippet"
        }
    ]
}

Provide at least 3-5 feedback items covering different aspects.
```

## Security Considerations

### API Key Management

- OpenAI API keys are stored as environment variables, not in code
- GitHub tokens are optional and only used for the specific request
- No API keys are stored in the database or logs

### Input Validation

- All user inputs are validated before processing
- Repository URLs and PR numbers are sanitized
- Error handling prevents exposure of sensitive information

### Rate Limiting

- OpenAI API calls are rate-limited to prevent abuse
- GitHub API calls respect the platform's rate limits
- Failed requests are handled gracefully with informative error messages

## Performance Optimization

### Caching

- PR data is cached to reduce API calls
- Analysis results are cached for repeated requests
- Cache invalidation occurs when PRs are updated

### Asynchronous Processing

- Long-running analyses are processed asynchronously
- Users receive immediate feedback while analysis runs
- Results are delivered when ready

## Future Enhancements

### Planned Features

1. **GitLab and Bitbucket Support**:
   - Full implementation of GitLab and Bitbucket connectors
   - Support for platform-specific features

2. **Advanced AI Models**:
   - Fine-tuned models for specific programming languages
   - Self-hosted models for improved privacy and cost control

3. **CI/CD Integration**:
   - GitHub Actions integration
   - GitLab CI integration
   - Jenkins plugin

4. **Team Collaboration**:
   - User accounts and team management
   - Customizable review policies
   - Historical analysis and trends

5. **Custom Rules Engine**:
   - User-defined rules for code quality
   - Organization-specific best practices
   - Rule templates and sharing

