# FastML WIP Production Deployment Guide

This guide covers deploying FastML Serve to production Kubernetes clusters (EKS, GKE, AKS, etc.).

## 🏗️ Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Production Kubernetes Cluster                │
├─────────────────────────────────────────────────────────────┤
│  Ingress Controller (nginx/traefik)                        │
│  ├─── https://fastml.example.com ────► Frontend UI         │
│  ├─── https://api.fastml.example.com ─► FastML API         │
│  ├─── https://grafana.fastml.example.com ─► Monitoring     │
│  └─── https://prometheus.fastml.example.com ─► Metrics     │
│                                                             │
│  Namespace: fastml-serve-{environment}                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastML    │  │  Frontend   │  │  Prometheus │        │  
│  │   Serve     │  │     UI      │  │   Metrics   │        │
│  │  (2-10 pods)│  │  (2 pods)   │  │  (1 pod)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │   Grafana   │  │ Container   │                         │
│  │ Dashboard   │  │  Registry   │                         │
│  │  (1 pod)    │  │ (External)  │                         │
│  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes Cluster**: EKS, GKE, AKS, or on-premise cluster
2. **Container Registry**: Docker Hub, ECR, GCR, ACR, or Harbor
3. **Domain**: Domain name with DNS control
4. **Ingress Controller**: nginx-ingress or traefik installed
5. **Cert-Manager**: For SSL/TLS certificates (optional but recommended)
6. **kubectl**: Configured for your cluster
7. **Docker**: For building images

### Environment Setup

1. **Configure registry credentials:**
   ```bash
   export DOCKER_USERNAME=your-username
   export DOCKER_PASSWORD=your-password
   export DOCKER_EMAIL=your-email@example.com
   ```

2. **Set deployment variables:**
   ```bash
   export REGISTRY=docker.io/yourusername  # or gcr.io/project-id
   export DOMAIN=fastml.example.com
   export ENVIRONMENT=prod
   export CLUSTER_CONTEXT=production-cluster
   ```

3. **Deploy to production:**
   ```bash
   # Full production deployment
   make -f Makefile.production deploy-prod \
     REGISTRY=$REGISTRY \
     DOMAIN=$DOMAIN \
     CLUSTER_CONTEXT=$CLUSTER_CONTEXT
   ```

## 📋 Deployment Commands

### Registry and Build Operations

```bash
# Login to container registry
make -f Makefile.production login-registry

# Build and push images
make -f Makefile.production build-push REGISTRY=docker.io/username

# Build locally (development)
make -f Makefile.production build
```

### Environment Deployment

```bash
# Deploy to development
make -f Makefile.production deploy-dev \
  REGISTRY=gcr.io/my-project \
  DOMAIN=dev.fastml.example.com

# Deploy to staging  
make -f Makefile.production deploy-staging \
  REGISTRY=gcr.io/my-project \
  DOMAIN=staging.fastml.example.com

# Deploy to production
make -f Makefile.production deploy-prod \
  REGISTRY=gcr.io/my-project \
  DOMAIN=fastml.example.com
```

### Service Management

```bash
# Check deployment status
make -f Makefile.production status ENVIRONMENT=prod

# View application logs
make -f Makefile.production logs ENVIRONMENT=prod

# Show service URLs
make -f Makefile.production urls ENVIRONMENT=prod DOMAIN=fastml.example.com

# Health check
make -f Makefile.production health ENVIRONMENT=prod
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENVIRONMENT` | Deployment environment | `dev` | `prod`, `staging` |
| `REGISTRY` | Container registry URL | `docker.io/yourusername` | `gcr.io/project-id` |
| `DOMAIN` | Base domain for services | `fastml.example.com` | `myapp.com` |
| `CLUSTER_CONTEXT` | Kubernetes context | `production-cluster` | `gke_project_zone_cluster` |
| `INGRESS_CLASS` | Ingress controller class | `nginx` | `traefik` |

### Container Registry Examples

**Docker Hub:**
```bash
REGISTRY=docker.io/username
```

**Google Container Registry:**
```bash
REGISTRY=gcr.io/project-id
```

**Amazon ECR:**
```bash
REGISTRY=123456789.dkr.ecr.region.amazonaws.com
```

**Azure Container Registry:**
```bash
REGISTRY=myregistry.azurecr.io
```

## 🌐 Service URLs

After deployment, services are accessible at:

- **Frontend UI**: `https://fastml.example.com`
- **API**: `https://api.fastml.example.com`
- **Grafana**: `https://grafana.fastml.example.com` (admin/admin123)
- **Prometheus**: `https://prometheus.fastml.example.com`

## 🔒 Security Features

### RBAC Configuration
- Service accounts with minimal permissions
- Role-based access control for each service
- Pod security contexts with non-root users

### Network Security
- Network policies restricting pod communication
- Ingress with SSL/TLS termination
- Rate limiting on public endpoints

### Secret Management
- Registry authentication via Kubernetes secrets
- Environment-specific configurations
- Grafana admin password (change default!)

### Container Security
- Non-root containers
- Read-only root filesystems
- Dropped capabilities
- Resource limits and quotas

## 📊 Monitoring and Observability

### Metrics Collection
- Prometheus scrapes metrics from FastML API
- Custom business metrics for predictions
- Infrastructure metrics for nodes and pods

### Dashboards
- Pre-configured Grafana dashboard
- Request rate, latency, and error metrics
- Resource usage and capacity planning

### Alerting Rules
- FastML server down alert
- High request latency warning
- High error rate critical alert
- Resource usage warnings

## 🔄 Model Management

### Dynamic Model Switching
```bash
# Change to different sentiment model
make -f Makefile.production change-model \
  MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest \
  ENVIRONMENT=prod

# Test current model
make -f Makefile.production test-model \
  TEXT="This is amazing!" \
  ENVIRONMENT=prod

# Check current model
make -f Makefile.production current-model ENVIRONMENT=prod
```

### Model Update Process
1. **ConfigMap Update**: Updates MODEL_NAME in Kubernetes ConfigMap
2. **Rolling Restart**: Restarts pods with zero downtime
3. **Health Checks**: Waits for deployment to be healthy
4. **Validation**: Tests new model with sample prediction

## 📈 Scaling and Performance

### Horizontal Pod Autoscaling (HPA)
- Automatic scaling based on CPU/memory usage
- Minimum: 2 replicas, Maximum: 10 replicas
- Target: 70% CPU, 80% Memory utilization

### Manual Scaling
```bash
# Scale to specific replica count
make -f Makefile.production scale REPLICAS=5 ENVIRONMENT=prod
```

### Rolling Updates
```bash
# Update with new image version
make -f Makefile.production rolling-update ENVIRONMENT=prod
```

## 🏥 Health Checks and Probes

### Readiness Probes
- API: `/health` endpoint check
- Frontend: HTTP 200 response check

### Liveness Probes
- Detect and restart unhealthy containers
- Configurable timeouts and failure thresholds

### Startup Probes
- Allow extra time for ML model loading
- Prevent premature restarts during initialization

## 🗂️ File Structure

```
k8s/production/
├── templates/
│   ├── deployment.yaml    # Application deployments
│   └── ingress.yaml      # Ingress configurations
├── rbac.yaml            # RBAC and security policies
├── prometheus.yaml      # Monitoring configuration
└── grafana.yaml        # Dashboard configuration

Makefile.production     # Production deployment commands
PRODUCTION-DEPLOYMENT.md # This documentation
```

## 🔧 Customization

### Environment-Specific Values
The production manifests use template variables that are replaced during deployment:

- `{{NAMESPACE}}`: Environment-specific namespace
- `{{ENVIRONMENT}}`: Current environment (dev/staging/prod)
- `{{API_IMAGE}}`: Full registry path to API image
- `{{FRONTEND_IMAGE}}`: Full registry path to frontend image
- `{{DOMAIN}}`: Base domain for ingress rules
- `{{INGRESS_CLASS}}`: Ingress controller class

### Resource Requirements
Modify resource limits in `deployment.yaml`:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi" 
    cpu: "1000m"
```

### Storage Classes
Update storage class for persistent volumes:

```yaml
storageClassName: fast-ssd  # Change to your preferred storage class
```

## 🚨 Troubleshooting

### Common Issues

**Images not pulling:**
```bash
# Check registry credentials
kubectl get secret registry-secret -n fastml-serve-prod -o yaml
```

**Ingress not working:**
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx
```

**SSL/TLS issues:**
```bash
# Check cert-manager
kubectl get certificates -n fastml-serve-prod
kubectl describe certificate fastml-serve-tls -n fastml-serve-prod
```

### Debug Commands

```bash
# Full debug information
make -f Makefile.production debug ENVIRONMENT=prod

# Describe problematic pods
make -f Makefile.production describe-pods ENVIRONMENT=prod

# Check events
kubectl get events -n fastml-serve-prod --sort-by='.lastTimestamp'
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      run: |
        echo "$KUBE_CONFIG" | base64 -d > ~/.kube/config
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
    
    - name: Login to registry
      run: |
        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
      env:
        DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
        DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Deploy to production
      run: |
        make -f Makefile.production deploy-prod \
          REGISTRY=${{ secrets.REGISTRY }} \
          DOMAIN=${{ secrets.DOMAIN }}
```

## 🧹 Cleanup

### Remove Environment
```bash
# Delete all resources in environment
make -f Makefile.production clean ENVIRONMENT=prod

# Delete entire namespace
make -f Makefile.production delete-namespace ENVIRONMENT=prod
```

## 📚 Additional Resources

- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [Prometheus Monitoring](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Container Registry Security](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)

---

## 🤝 Support

For production deployment issues:
1. Check the troubleshooting section
2. Review Kubernetes events and logs
3. Verify network and security configurations
4. Consult your platform-specific documentation (EKS/GKE/AKS)