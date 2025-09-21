# PR Review Agent - Setup Instructions

## 🚀 Quick Setup Guide

### 1. Prerequisites
- Python 3.8+
- Hugging Face account and API token

### 2. Get Hugging Face API Token
1. Go to [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Create a new token with "Read" permissions
3. Copy the token (starts with `hf_...`)

### 3. Environment Setup

#### For Windows PowerShell:
```powershell
# Navigate to project directory
cd pr_review_agent

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Set environment variables (PowerShell syntax)
$env:HF_TOKEN="your_huggingface_token_here"
$env:GITHUB_TOKEN="your_github_token_here"  # Optional, for private repos

# Install dependencies
pip install -r requirements.txt
```

#### For Unix/Linux/macOS:
```bash
# Extract the project
tar -xzf pr_review_agent_qwen_final.tar.gz
cd pr_review_agent

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export HF_TOKEN="your_huggingface_token_here"
export GITHUB_TOKEN="your_github_token_here"  # Optional, for private repos

# Install dependencies (already included in venv)
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python src/main.py
```

The application will be available at: http://localhost:5000

### 5. Test the Application
1. Open http://localhost:5000 in your browser
2. Enter a GitHub PR URL (e.g., `https://github.com/owner/repo/pull/123`)
3. Click "Analyze PR" to get AI-powered feedback

## 🔧 Key Features

- **AI Model**: Uses Mistral-7B-Instruct from Hugging Face
- **No Database**: All processing is done in-memory
- **Multi-platform**: GitHub support (GitLab/Bitbucket ready)
- **Quality Scoring**: Comprehensive code quality assessment
- **Inline Comments**: Line-specific feedback and suggestions

## 📝 API Endpoints

- `GET /api/review/health` - Check service status
- `POST /api/review/analyze` - Analyze a pull request
- `GET /` - Web interface

## 🐛 Troubleshooting

### AI Analyzer Unavailable
- Ensure `HF_TOKEN` environment variable is set
- Verify your Hugging Face token has proper permissions
- Check internet connectivity for API calls

### GitHub API Issues
- Set `GITHUB_TOKEN` for private repositories
- Verify the PR URL format is correct
- Check GitHub API rate limits

## 🎯 Hackathon Submission Notes

This project implements:
- ✅ Multi-platform PR analysis
- ✅ AI-powered code review using Hugging Face Mistral model
- ✅ Quality scoring system
- ✅ Web interface and API
- ✅ Inline comments and suggestions
- ✅ No database dependency (in-memory processing)

Perfect for CodeMate Hackathon Problem 2 requirements!

