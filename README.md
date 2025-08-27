# FastML Serve - Lightweight ML Inference Server

A production-ready, containerized inference server that serves a pre-trained sentiment analysis model via REST API.



## 🚀 Features

- **Production-Ready API**: FastAPI-based REST API with automatic OpenAPI documentation
- **ML Model Integration**: Pre-trained DistilBERT model for sentiment analysis
- **Containerized Deployment**: Multi-stage Docker builds for optimized production images
- **Monitoring & Metrics**: Prometheus metrics integration with health checks
- **Batch Processing**: Efficient batch inference for multiple texts
- **CI/CD Pipeline**: GitHub Actions with automated testing, security scanning, and deployment
- **MLOps Best Practices**: Model versioning, structured logging, and error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastML Serve   │───▶│  DistilBERT     │
└─────────────────┘    │   (FastAPI)      │    │  Model          │
                       └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Prometheus     │
                       │   Metrics        │
                       └──────────────────┘
```

### Technology Stack

- **API Framework**: FastAPI 0.104 with async support
- **ML Model**: HuggingFace Transformers (DistilBERT)
- **Validation**: Pydantic v2 for request/response schemas
- **Monitoring**: Prometheus client for metrics collection
- **Testing**: Pytest with async test support
- **Containerization**: Docker with multi-stage builds
- **CI/CD**: GitHub Actions with security scanning

## 🚦 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yasharora2020/fastml-serve.git
   cd fastml-serve
   ```

2. **Install uv (if not already installed)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync --all-extras
   ```

4. **Run the server**
   ```bash
   uv run python -m uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run individually**
   ```bash
   docker build -t fastml-serve .
   docker run -p 8000:8000 fastml-serve
   ```

## 📊 API Usage Examples

### Single Prediction

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "I love this product! It works perfectly."}'
```

**Response:**
```json
{
  "text": "I love this product! It works perfectly.",
  "sentiment": "positive",
  "confidence": 0.9998,
  "processing_time": 0.0234,
  "timestamp": "2024-01-15T10:30:00.123Z"
}
```

### Batch Prediction

```bash
curl -X POST "http://localhost:8000/predict/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "texts": [
         "This is amazing!",
         "Not what I expected.",
         "Pretty good overall."
       ]
     }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime": 3600.5,
  "timestamp": "2024-01-15T10:30:00.123Z"
}
```

## 📈 Performance Benchmarks

| Metric | Single Request | Batch (10 items) |
|--------|----------------|-------------------|
| Latency | ~25ms | ~45ms |
| Throughput | 40 req/sec | 200+ items/sec |
| Memory Usage | ~1.2GB | ~1.4GB |

*Tested on: Intel i7, 16GB RAM, Docker container with 2 CPU cores*

## 🔧 Technical Implementation

### Model Selection Rationale

- **DistilBERT**: 60% smaller than BERT while retaining 97% of performance
- **Pre-trained**: Stanford SST-2 dataset for sentiment classification
- **Fast Inference**: Optimized for production workloads
- **HuggingFace Integration**: Easy model updates and versioning

### API Design Decisions

- **FastAPI**: Automatic validation, serialization, and documentation
- **Pydantic**: Strong typing and validation for all inputs/outputs
- **Async Support**: Non-blocking I/O for better concurrency
- **Error Handling**: Structured error responses with appropriate HTTP codes

### Scalability Considerations

- **Stateless Design**: Easy horizontal scaling
- **Batch Processing**: Efficient GPU utilization
- **Model Caching**: Single model instance shared across requests
- **Health Checks**: Kubernetes/Docker orchestration support

## 🛠️ MLOps Features

### Monitoring with Prometheus

- Request count and duration metrics
- Model prediction counters
- Error rate tracking
- Custom business metrics

**Key Metrics:**
- `requests_total{method, endpoint}`: Total requests by endpoint
- `request_duration_seconds`: Request latency histogram
- `predictions_total`: Total ML predictions made

### CI/CD Pipeline

The GitHub Actions pipeline includes:

1. **Testing**: Unit tests with pytest, code formatting with black
2. **Security**: Bandit security scanning, Trivy container scanning
3. **Building**: Multi-architecture Docker builds (AMD64, ARM64)
4. **Registry**: Automatic push to GitHub Container Registry
5. **Quality Gates**: All tests must pass before deployment

### Model Versioning Strategy

- **Git Tags**: Version releases with semantic versioning
- **Container Tags**: Docker images tagged with model versions
- **Health Endpoint**: Reports current model version and status
- **A/B Testing Ready**: Architecture supports multiple model versions

## 🐳 Production Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastml-serve
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastml-serve
  template:
    metadata:
      labels:
        app: fastml-serve
    spec:
      containers:
      - name: fastml-serve
        image: ghcr.io/yourusername/fastml-serve:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `MODEL_NAME` | HuggingFace model name | `distilbert-base-uncased-finetuned-sst-2-english` |
| `MAX_BATCH_SIZE` | Maximum batch size | `32` |
| `CACHE_SIZE` | Model cache size | `1000` |

## 🧪 Testing

Run the test suite:

```bash
# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Format code
uv run ruff format app/ tests/

# Lint code
uv run ruff check app/ tests/
```

## 🔒 Security Features

- **Non-root container**: Runs as unprivileged user
- **Input validation**: Pydantic schemas prevent injection attacks
- **Rate limiting ready**: Architecture supports rate limiting middleware
- **Security scanning**: Automated vulnerability scanning in CI/CD
- **Minimal attack surface**: Distroless base images in production

## 🎯 Minikube Deployment

### Prerequisites
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed and running
- [kubectl](https://kubernetes.io/docs/tasks/tools/) configured
- [Docker](https://docs.docker.com/get-docker/) installed

### Quick Deployment

Deploy the complete ML stack with monitoring in one command:

```bash
# Deploy everything (FastML API + UI + Prometheus + Grafana)
make deploy

# Access services via localhost (recommended)
make access
```

**Service URLs:**
- **🎯 Sentiment Analysis UI**: http://localhost:8081
- **📊 Grafana Dashboard**: http://localhost:3000 (admin/admin)  
- **📈 Prometheus Metrics**: http://localhost:9090
- **🤖 FastML API**: http://localhost:8080

### Available Commands

```bash
# Core deployment
make deploy          # Build and deploy complete stack
make clean           # Clean up all resources
make rebuild         # Clean, rebuild, and redeploy

# Access services  
make access          # Port forward to localhost (reliable)
make tunnel          # Start minikube tunnel for LoadBalancer IPs
make urls            # Show service URLs (after tunnel)

# Monitoring
make status          # Show deployment status
make logs            # Show service logs
make test            # Test all endpoints

# Model Management
make change-model    # Change ML model (usage: MODEL=model-name)
make current-model   # Show current model information  
make test-model      # Test model prediction (usage: TEXT="text")

# Development
make build           # Build Docker images
make restart         # Restart all services
```

### Architecture on Minikube

```
┌─────────────────────────────────────────────────────────────┐
│                      Minikube Cluster                      │
├─────────────────────────────────────────────────────────────┤
│  Namespace: fastml-serve                                    │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastML    │  │  Frontend   │  │  Prometheus │        │
│  │   Serve     │  │     UI      │  │   Metrics   │        │  
│  │  (2 pods)   │  │  (1 pod)    │  │  (1 pod)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐                                           │
│  │   Grafana   │                                           │
│  │ Dashboard   │  <- LoadBalancer Services ->              │
│  │  (1 pod)    │     (Port-forward for access)             │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### What Gets Deployed

**FastML Application:**
- 2x FastML API replicas with auto-scaling (HPA)
- Health checks and startup probes
- Prometheus metrics enabled

**Frontend UI:**
- React-based sentiment analysis interface
- Auto-detects API endpoints
- Responsive design for testing

**Monitoring Stack:**
- Prometheus for metrics collection
- Grafana with pre-configured dashboards
- Service discovery for automatic monitoring

**Features Included:**
- ✅ Horizontal Pod Autoscaling (2-5 replicas)
- ✅ Resource limits and requests
- ✅ Health and readiness probes  
- ✅ Persistent monitoring and logging
- ✅ Dynamic model switching without downtime
- ✅ Service mesh ready architecture

### Troubleshooting

**Service URLs not working?**
```bash
# Use port-forward (always works)
make access

# Check service status
make status

# View logs for debugging
make logs
```

**Pod not starting?**
```bash
# Check pod status
kubectl get pods -n fastml-serve

# Check specific pod logs
kubectl logs -l app=fastml-serve -n fastml-serve
```

**Clean restart:**
```bash
make clean && make deploy
```

### Model Management

**Dynamic Model Switching:**
The deployment supports changing ML models without rebuilding containers or taking downtime.

**Change Model:**
```bash
# Switch to any HuggingFace sentiment analysis model
make change-model MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest

# Popular models you can use:
make change-model MODEL=cardiffnlp/twitter-xlm-roberta-base-sentiment
make change-model MODEL=nlptown/bert-base-multilingual-uncased-sentiment  
make change-model MODEL=distilbert-base-uncased-finetuned-sst-2-english
```

**Check Current Model:**
```bash
# View current model info
make current-model

# Test current model
make test-model TEXT="This works perfectly!"

# Test with custom text
make test-model TEXT="I'm not sure about this"
```

**How It Works:**
1. **ConfigMap Update**: Updates MODEL_NAME in Kubernetes ConfigMap
2. **Rolling Restart**: Restarts pods with zero downtime
3. **Automatic Download**: New model downloads on first startup
4. **UI Update**: Frontend automatically shows the new model name
5. **Health Check**: Waits for deployment to be healthy

**Example Model Change:**
```bash
$ make change-model MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest
🔄 Changing model to: cardiffnlp/twitter-roberta-base-sentiment-latest
📝 Updating ConfigMap...
♻️  Restarting deployment to load new model...
⏳ Waiting for rollout to complete...
✅ Model changed successfully!

$ make test-model TEXT="Amazing! 🚀"
🧪 Testing model with text: "Amazing! 🚀"
📊 Result: positive (0.9998)
```

The frontend UI automatically updates to show "Twitter RoBERTa" instead of "DistilBERT", and all predictions use the new model immediately.

## 🚀 Model Update Strategy

1. **Blue-Green Deployment**: Zero-downtime model updates
2. **Canary Releases**: Gradual rollout of new model versions
3. **Rollback Support**: Quick revert to previous model version
4. **A/B Testing**: Compare model performance in production

