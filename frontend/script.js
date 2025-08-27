class SentimentAnalyzer {
    constructor() {
        // Detect if running in cluster or locally
        this.baseUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8080'  // Local development
            : `http://${window.location.hostname}:30080`; // Kubernetes NodePort
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkServiceStatus();
        this.setupCharacterCounter();
    }

    setupEventListeners() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        const batchBtn = document.getElementById('batchBtn');
        const textInput = document.getElementById('textInput');

        analyzeBtn.addEventListener('click', () => this.analyzeSingle());
        batchBtn.addEventListener('click', () => this.analyzeBatch());
        
        // Allow Enter key to trigger analysis
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.analyzeSingle();
            }
        });
    }

    setupCharacterCounter() {
        const textInput = document.getElementById('textInput');
        const charCount = document.getElementById('charCount');

        textInput.addEventListener('input', () => {
            const count = textInput.value.length;
            charCount.textContent = count;
            charCount.style.color = count > 450 ? '#e74c3c' : '#666';
        });
    }

    async checkServiceStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const data = await response.json();
            
            this.updateServiceStatus('healthy', data);
        } catch (error) {
            this.updateServiceStatus('error', null);
            console.error('Service health check failed:', error);
        }
    }

    updateServiceStatus(status, data) {
        const statusElement = document.getElementById('serviceStatus');
        const uptimeElement = document.getElementById('uptime');
        const modelNameElement = document.getElementById('modelName');
        const subtitleElement = document.getElementById('subtitle');

        if (status === 'healthy') {
            statusElement.textContent = '✅ Online';
            statusElement.className = 'stat-value status-healthy';
            
            if (data && data.uptime) {
                const uptimeMinutes = Math.round(data.uptime / 60);
                uptimeElement.textContent = `${uptimeMinutes}m`;
            }

            if (data && data.model_name) {
                // Display shortened model name
                const modelName = this.getDisplayModelName(data.model_name);
                modelNameElement.textContent = modelName;
                subtitleElement.textContent = `Real-time Sentiment Analysis with ${modelName}`;
            }
        } else {
            statusElement.textContent = '❌ Offline';
            statusElement.className = 'stat-value status-error';
            uptimeElement.textContent = '-';
            modelNameElement.textContent = 'Unknown';
            subtitleElement.textContent = 'Real-time Sentiment Analysis';
        }
    }

    getDisplayModelName(fullModelName) {
        // Convert model names to user-friendly display names
        const modelMappings = {
            'distilbert-base-uncased-finetuned-sst-2-english': 'DistilBERT',
            'cardiffnlp/twitter-roberta-base-sentiment-latest': 'Twitter RoBERTa',
            'cardiffnlp/twitter-xlm-roberta-base-sentiment': 'XLM-RoBERTa',
            'nlptown/bert-base-multilingual-uncased-sentiment': 'Multilingual BERT'
        };

        // Return mapped name or shortened version of the original
        if (modelMappings[fullModelName]) {
            return modelMappings[fullModelName];
        }

        // For unknown models, try to extract a meaningful name
        const parts = fullModelName.split('/');
        const modelPart = parts[parts.length - 1];
        
        // Convert kebab-case to Title Case and limit length
        const displayName = modelPart
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')
            .substring(0, 20);

        return displayName || 'Custom Model';
    }

    async analyzeSingle() {
        const textInput = document.getElementById('textInput');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const text = textInput.value.trim();

        if (!text) {
            this.showError('Please enter some text to analyze');
            return;
        }

        if (text.length > 512) {
            this.showError('Text is too long. Maximum 512 characters allowed.');
            return;
        }

        this.setButtonLoading(analyzeBtn, true);

        try {
            const response = await fetch(`${this.baseUrl}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            this.displayResults([{
                text: text,
                sentiment: result.sentiment,
                confidence: result.confidence
            }]);

        } catch (error) {
            console.error('Analysis failed:', error);
            this.showError(`Analysis failed: ${error.message}`);
        } finally {
            this.setButtonLoading(analyzeBtn, false);
        }
    }

    async analyzeBatch() {
        const batchInput = document.getElementById('batchInput');
        const batchBtn = document.getElementById('batchBtn');
        const texts = batchInput.value.trim().split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);

        if (texts.length === 0) {
            this.showError('Please enter some texts to analyze (one per line)');
            return;
        }

        if (texts.length > 32) {
            this.showError('Too many texts. Maximum 32 texts allowed for batch analysis.');
            return;
        }

        this.setButtonLoading(batchBtn, true);

        try {
            const response = await fetch(`${this.baseUrl}/predict/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ texts: texts })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            const formattedResults = result.results.map((res, index) => ({
                text: texts[index],
                sentiment: res.sentiment,
                confidence: res.confidence
            }));

            this.displayResults(formattedResults);

        } catch (error) {
            console.error('Batch analysis failed:', error);
            this.showError(`Batch analysis failed: ${error.message}`);
        } finally {
            this.setButtonLoading(batchBtn, false);
        }
    }

    displayResults(results) {
        const resultsSection = document.getElementById('results');
        const resultsContent = document.getElementById('resultsContent');

        resultsContent.innerHTML = '';

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = `result-item ${result.sentiment.toLowerCase()}`;

            const confidencePercent = Math.round(result.confidence * 100);
            
            resultDiv.innerHTML = `
                <div class="result-text">"${result.text}"</div>
                <div class="result-details">
                    <span class="sentiment-label">${result.sentiment}</span>
                    <span class="confidence">${confidencePercent}%</span>
                </div>
            `;

            resultsContent.appendChild(resultDiv);
        });

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    setButtonLoading(button, isLoading) {
        const btnText = button.querySelector('.btn-text');
        const btnLoader = button.querySelector('.btn-loader');

        if (isLoading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
            button.disabled = true;
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            button.disabled = false;
        }
    }

    showError(message) {
        const resultsSection = document.getElementById('results');
        const resultsContent = document.getElementById('resultsContent');

        resultsContent.innerHTML = `
            <div class="error-message">
                <strong>Error:</strong> ${message}
            </div>
        `;

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SentimentAnalyzer();
});

// Optional: Auto-refresh service status every 30 seconds
setInterval(() => {
    if (window.sentimentAnalyzer) {
        window.sentimentAnalyzer.checkServiceStatus();
    }
}, 30000);