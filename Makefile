.PHONY: all build deploy clean test monitor status help build-images deploy-all

# Default target
all: build deploy

# Variables
NAMESPACE := fastml-serve
APP_IMAGE := fastml-serve:latest
FRONTEND_IMAGE := fastml-frontend:latest
MINIKUBE_IP := $(shell minikube ip)

help: ## Show this help message
	@echo "FastML Deployment Makefile"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: build-images ## Build all Docker images

build-images: ## Build Docker images in minikube context
	@echo "🔨 Building Docker images..."
	@eval $$(minikube -p minikube docker-env) && \
	docker build -t $(APP_IMAGE) . && \
	cd frontend && docker build -t $(FRONTEND_IMAGE) .
	@echo "✅ Docker images built successfully"

deploy: deploy-all ## Deploy complete stack to minikube

deploy-all: ## Deploy all services to Kubernetes
	@echo "🚀 Deploying complete FastML stack..."
	@echo "📦 Creating namespace..."
	@kubectl apply -f k8s/namespace.yaml
	@echo "🔍 Deploying monitoring stack..."
	@kubectl apply -f k8s/prometheus.yaml
	@kubectl apply -f k8s/grafana.yaml
	@echo "⚡ Deploying FastML application..."
	@kubectl apply -f k8s/deployment.yaml
	@kubectl apply -f k8s/hpa.yaml
	@kubectl apply -f k8s/ingress.yaml
	@echo "🌐 Deploying frontend UI..."
	@kubectl apply -f k8s/frontend.yaml
	@echo "⏳ Waiting for deployments to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment/fastml-serve -n $(NAMESPACE)
	@kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n $(NAMESPACE)
	@kubectl wait --for=condition=available --timeout=300s deployment/grafana -n $(NAMESPACE)
	@kubectl wait --for=condition=available --timeout=300s deployment/frontend -n $(NAMESPACE)
	@echo "✅ All services deployed successfully!"
	@echo ""
	@echo "🔗 To access your application:"
	@echo "   Option 1 (Recommended): make access  # Reliable localhost access"
	@echo "   Option 2: make tunnel   # Then use 'make urls' for LoadBalancer IPs"
	@echo ""
	@echo "📖 Quick Commands:"
	@echo "   make access - Port forward all services to localhost"
	@echo "   make urls   - Show LoadBalancer URLs (requires tunnel)"
	@echo "   make status - Show deployment status"
	@echo ""

status: ## Show deployment status
	@echo "📊 FastML Stack Status:"
	@echo "Namespace: $(NAMESPACE)"
	@echo ""
	@kubectl get all -n $(NAMESPACE)
	@echo ""
	@echo "🔗 Service URLs (requires 'make tunnel'):"
	@echo "  FastML API:    $$(kubectl get service fastml-serve-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'pending'):8000"
	@echo "  Frontend UI:   $$(kubectl get service frontend-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'pending'):80"
	@echo "  Prometheus:    $$(kubectl get service prometheus-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'pending'):9090"
	@echo "  Grafana:       $$(kubectl get service grafana-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'pending'):3000 (admin/admin)"

test: ## Test the deployed services
	@echo "🧪 Testing deployed services..."
	@echo "Testing FastML API health endpoint..."
	@curl -s http://$(MINIKUBE_IP):30080/health | jq '.' || echo "❌ FastML API not responding"
	@echo ""
	@echo "Testing sentiment analysis endpoint..."
	@curl -s -X POST http://$(MINIKUBE_IP):30080/predict \
		-H "Content-Type: application/json" \
		-d '{"text":"I love this application!"}' | jq '.' || echo "❌ Prediction endpoint not responding"
	@echo ""
	@echo "Testing Frontend UI..."
	@curl -s -o /dev/null -w "Frontend UI: %{http_code}\n" http://$(MINIKUBE_IP):30081/ || echo "❌ Frontend not responding"
	@echo "Testing Prometheus..."
	@curl -s -o /dev/null -w "Prometheus: %{http_code}\n" http://$(MINIKUBE_IP):30090/-/ready || echo "❌ Prometheus not responding"
	@echo "Testing Grafana..."
	@curl -s -o /dev/null -w "Grafana: %{http_code}\n" http://$(MINIKUBE_IP):30300/api/health || echo "❌ Grafana not responding"

monitor: ## Open monitoring dashboards
	@echo "🖥️  Opening monitoring dashboards..."
	@echo "Opening Grafana dashboard..."
	@open http://$(MINIKUBE_IP):30300 || echo "Please open http://$(MINIKUBE_IP):30300 manually"
	@echo "Opening Prometheus..."
	@open http://$(MINIKUBE_IP):30090 || echo "Please open http://$(MINIKUBE_IP):30090 manually"
	@echo "Opening Frontend UI..."
	@open http://$(MINIKUBE_IP):30081 || echo "Please open http://$(MINIKUBE_IP):30081 manually"

logs: ## Show logs from all services
	@echo "📝 Recent logs from all services:"
	@echo "=== FastML Service Logs ==="
	@kubectl logs -l app=fastml-serve -n $(NAMESPACE) --tail=20
	@echo ""
	@echo "=== Prometheus Logs ==="
	@kubectl logs -l app=prometheus -n $(NAMESPACE) --tail=10
	@echo ""
	@echo "=== Grafana Logs ==="
	@kubectl logs -l app=grafana -n $(NAMESPACE) --tail=10

clean: ## Clean up all deployed resources
	@echo "🧹 Cleaning up FastML deployment..."
	@kubectl delete namespace $(NAMESPACE) --ignore-not-found=true
	@echo "✅ Cleanup completed"

restart: ## Restart all deployments
	@echo "♻️  Restarting all deployments..."
	@kubectl rollout restart deployment/fastml-serve -n $(NAMESPACE)
	@kubectl rollout restart deployment/prometheus -n $(NAMESPACE)
	@kubectl rollout restart deployment/grafana -n $(NAMESPACE)
	@kubectl rollout restart deployment/frontend -n $(NAMESPACE)
	@echo "✅ All deployments restarted"

rebuild: clean build deploy ## Clean, rebuild, and redeploy everything

change-model: ## Change ML model (usage: make change-model MODEL=model-name)
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Error: MODEL parameter required"; \
		echo "Usage: make change-model MODEL=model-name"; \
		echo ""; \
		echo "Popular sentiment models:"; \
		echo "  cardiffnlp/twitter-roberta-base-sentiment-latest"; \
		echo "  nlptown/bert-base-multilingual-uncased-sentiment"; \
		echo "  distilbert-base-uncased-finetuned-sst-2-english"; \
		echo "  cardiffnlp/twitter-xlm-roberta-base-sentiment"; \
		exit 1; \
	fi
	@echo "🔄 Changing model to: $(MODEL)"
	@echo "📝 Updating ConfigMap..."
	@kubectl patch configmap fastml-serve-config -n $(NAMESPACE) -p '{"data":{"MODEL_NAME":"$(MODEL)"}}'
	@echo "♻️  Restarting deployment to load new model..."
	@kubectl rollout restart deployment/fastml-serve -n $(NAMESPACE)
	@echo "⏳ Waiting for rollout to complete..."
	@kubectl rollout status deployment/fastml-serve -n $(NAMESPACE)
	@echo "✅ Model changed successfully!"
	@echo ""
	@echo "🧪 Test the new model:"
	@echo "  make test-model TEXT=\"Your test text here\""

test-model: ## Test current model (usage: make test-model TEXT="test text")
	@if [ -z "$(TEXT)" ]; then \
		TEXT="This is amazing! I love it."; \
	fi
	@echo "🧪 Testing model with text: \"$(TEXT)\""
	@RESULT=$$(curl -s -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d "{\"text\":\"$(TEXT)\"}" 2>/dev/null || echo "error"); \
	if [ "$$RESULT" = "error" ]; then \
		echo "❌ API not accessible. Run 'make access' first."; \
	else \
		SENTIMENT=$$(echo "$$RESULT" | jq -r '.sentiment // "error"' 2>/dev/null || echo "parse_error"); \
		CONFIDENCE=$$(echo "$$RESULT" | jq -r '.confidence // "N/A"' 2>/dev/null | cut -c1-6); \
		echo "📊 Result: $$SENTIMENT ($$CONFIDENCE)"; \
		echo "📈 Full response:"; \
		echo "$$RESULT" | jq . 2>/dev/null || echo "$$RESULT"; \
	fi

current-model: ## Show current model information
	@echo "🤖 Current Model Information:"
	@echo "ConfigMap MODEL_NAME: $$(kubectl get configmap fastml-serve-config -n $(NAMESPACE) -o jsonpath='{.data.MODEL_NAME}' 2>/dev/null || echo 'not found')"
	@HEALTH=$$(curl -s http://localhost:8080/health 2>/dev/null || echo "api_unavailable"); \
	if [ "$$HEALTH" != "api_unavailable" ]; then \
		echo "API Status: $$(echo $$HEALTH | jq -r '.status // "unknown"')"; \
		echo "Model Loaded: $$(echo $$HEALTH | jq -r '.model_loaded // "unknown"')"; \
		echo "Uptime: $$(echo $$HEALTH | jq -r '.uptime // "unknown"')s"; \
	else \
		echo "❌ API not accessible. Run 'make access' first."; \
	fi

tunnel: ## Start minikube tunnel (required for LoadBalancer services)
	@echo "🚇 Starting minikube tunnel..."
	@echo "⚠️  Keep this terminal open - tunnel must remain active"
	@echo "🔗 After tunnel starts, services will be available with 'make urls'"
	@echo "   Press Ctrl+C to stop the tunnel"
	@echo ""
	@minikube tunnel

urls: ## Show service URLs (after tunnel is running)
	@echo "🔗 Service URLs:"
	@echo ""
	@FASTML_IP=$$(kubectl get service fastml-serve-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null); \
	FRONTEND_IP=$$(kubectl get service frontend-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null); \
	PROMETHEUS_IP=$$(kubectl get service prometheus-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null); \
	GRAFANA_IP=$$(kubectl get service grafana-service -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null); \
	if [ -z "$$FRONTEND_IP" ] || [ "$$FRONTEND_IP" = "null" ]; then \
		echo "⚠️  LoadBalancer IPs not assigned yet."; \
		echo "   Make sure 'make tunnel' is running in another terminal."; \
		echo "   Or use 'make access' for reliable localhost access."; \
		echo ""; \
		echo "💡 Recommended: Use 'make access' for immediate access"; \
	else \
		echo "  🎯 Sentiment Analysis UI: http://$$FRONTEND_IP"; \
		echo "  📊 Grafana Dashboard:     http://$$GRAFANA_IP:3000 (admin/admin)"; \
		echo "  📈 Prometheus Metrics:    http://$$PROMETHEUS_IP:9090"; \
		echo "  🤖 FastML API:           http://$$FASTML_IP:8000"; \
	fi

access: ## Set up port forwarding for reliable localhost access
	@echo "🔌 Setting up port forwarding for localhost access..."
	@echo "Services will be available at:"
	@echo "  Sentiment Analysis UI: http://localhost:8081"
	@echo "  Grafana Dashboard:     http://localhost:3000 (admin/admin)"
	@echo "  Prometheus Metrics:    http://localhost:9090"
	@echo "  FastML API:           http://localhost:8080"
	@echo ""
	@echo "Press Ctrl+C to stop all port forwards"
	@echo "Starting port forwards..."
	@kubectl port-forward -n $(NAMESPACE) service/frontend-service 8081:80 &
	@kubectl port-forward -n $(NAMESPACE) service/grafana-service 3000:3000 &
	@kubectl port-forward -n $(NAMESPACE) service/prometheus-service 9090:9090 &
	@kubectl port-forward -n $(NAMESPACE) service/fastml-serve-service 8080:8000 &
	@echo "All services now accessible via localhost URLs above"
	@echo "Press Ctrl+C to stop"
	@wait

port-forward: access ## Alias for access command