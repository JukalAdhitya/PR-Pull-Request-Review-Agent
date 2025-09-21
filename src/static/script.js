class PRReviewAgent {
  constructor() {
    this.apiBaseUrl = '/api/review';
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    document.getElementById('reviewForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.analyzePullRequest();
    });

    document.getElementById('demoBtn').addEventListener('click', () => {
      this.runDemo();
    });
  }

  async analyzePullRequest() {
    const formData = this.getFormData();
    if (!this.validateFormData(formData)) return;

    this.toggleLoading(true);
    this.hideResults();

    try {
      const response = await fetch(`${this.apiBaseUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      this.displayResults(data);
    } catch (err) {
      this.showError(`Analysis failed: ${err.message}`);
    } finally {
      this.toggleLoading(false);
    }
  }

  async runDemo() {
    this.toggleLoading(true);
    this.hideResults();

    try {
      const response = await fetch(`${this.apiBaseUrl}/demo`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      this.displayResults(data);
    } catch (err) {
      this.showError(`Demo failed: ${err.message}`);
    } finally {
      this.toggleLoading(false);
    }
  }

  getFormData() {
    return {
      platform: document.getElementById('platform').value,
      repo_url: document.getElementById('repoUrl').value.trim(),
      pr_number: parseInt(document.getElementById('prNumber').value),
      github_token: document.getElementById('githubToken').value.trim() || undefined
    };
  }

  validateFormData(data) {
    if (!data.repo_url) return this.showError('Repository URL is required');
    if (!data.pr_number || isNaN(data.pr_number)) return this.showError('Valid PR number required');
    return true;
  }

  displayResults(data) {
    document.getElementById('resultsSection').style.display = 'block';

    const prInfo = data.pr_info || {};
    document.getElementById('prInfo').innerHTML = `
      <div class="feedback-item">
        <strong>Title:</strong> ${prInfo.title || 'N/A'}<br/>
        <strong>Author:</strong> ${prInfo.author || 'N/A'}<br/>
        <strong>Status:</strong> ${prInfo.status || 'N/A'}<br/>
        <strong>Files Changed:</strong> ${prInfo.files_changed || 0}<br/>
        ${prInfo.pr_url ? `<a href="${prInfo.pr_url}" target="_blank">View PR</a>` : ''}
      </div>`;

    const score = data.review_result?.quality_score?.overall_score || 0;
    const grade = this.calculateGrade(score);
    document.getElementById('qualityScore').innerHTML = `
      <div class="score-card">
        <div class="score-circle grade-${grade.toLowerCase()}">${grade}</div>
        <h4 class="text-center">${score.toFixed(1)}/100</h4>
      </div>`;

    const feedback = data.review_result?.feedback_items || [];
    document.getElementById('feedbackItems').innerHTML = feedback.length
      ? feedback.map(item => `
        <div class="feedback-item severity-${(item.severity || 'low').toLowerCase()}">
          <strong>${item.type}:</strong> ${item.message}
          ${item.suggestion ? `<br/><em>Suggestion:</em> ${item.suggestion}` : ''}
        </div>`).join('')
      : '<div class="feedback-item text-success">No major issues found!</div>';

    const recommendations = data.review_result?.recommendations || [];
    document.getElementById('recommendations').innerHTML = recommendations.length
      ? `<div class="feedback-item"><strong>Recommendations:</strong><ul>${recommendations.map(r => `<li>${r}</li>`).join('')}</ul></div>`
      : '';
  }

  calculateGrade(score) {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  toggleLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = show ? 'block' : 'none';
  }

  hideResults() {
    document.getElementById('resultsSection').style.display = 'none';
  }

  showError(message) {
    document.getElementById('resultsSection').innerHTML = `
      <div style="background:#1e293b; color:#ff6b6b; border:1px solid #ef4444; box-shadow:0 0 20px #ef4444; padding:1rem; border-radius:10px;">
        <h4><i class="fas fa-exclamation-triangle"></i> ${message}</h4>
      </div>`;
    document.getElementById('resultsSection').style.display = 'block';
  }
}

document.addEventListener('DOMContentLoaded', () => new PRReviewAgent());
