.PHONY: help build deploy undeploy clean logs port-forward

# Variables
CLUSTER_NAME=devlab
FRONTEND_IMAGE=hubbops-frontend:latest
BACKEND_IMAGE=hubbops-backend:latest

help: ## Show this help
	@echo "Hubbops Platform - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	@echo "🔨 Building frontend image..."
	docker build -f Dockerfile.frontend -t $(FRONTEND_IMAGE) .
	@echo "🔨 Building backend image..."
	docker build -f Dockerfile.backend -t $(BACKEND_IMAGE) .
	@echo "✅ Images built successfully"

import: build ## Import images to K3d
	@echo "📦 Importing images to K3d cluster..."
	k3d image import $(FRONTEND_IMAGE) -c $(CLUSTER_NAME)
	k3d image import $(BACKEND_IMAGE) -c $(CLUSTER_NAME)
	@echo "✅ Images imported"

deploy: import ## Deploy Hubbops to K3d
	@echo "🚀 Deploying Hubbops platform..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/backend.yaml
	kubectl apply -f k8s/frontend.yaml
	kubectl apply -f k8s/ingress.yaml
	@echo "⏳ Waiting for pods to be ready..."
	kubectl wait --for=condition=ready pod -l app=hubbops-backend -n hubbops --timeout=120s
	kubectl wait --for=condition=ready pod -l app=hubbops-frontend -n hubbops --timeout=120s
	@echo ""
	@echo "✅ Hubbops deployed successfully!"
	@echo ""
	@echo "📍 Access:"
	@echo "   Frontend: http://hubbops.local (via port-forward or Ingress)"
	@echo "   Backend:  http://hubbops.local/api"
	@echo ""
	@echo "🔧 Next steps:"
	@echo "   make port-forward  - Forward ports to localhost"
	@echo "   make logs          - View logs"

port-forward: ## Forward ports to localhost
	@echo "🔌 Port forwarding..."
	@echo "   Frontend: http://localhost:8080"
	@echo "   Backend:  http://localhost:8000"
	@kubectl port-forward -n hubbops svc/hubbops-frontend 8080:80 &
	@kubectl port-forward -n hubbops svc/hubbops-backend 8000:8000 &
	@echo "✅ Port forwarding active (Ctrl+C to stop)"

logs: ## View logs
	@echo "📋 Viewing logs..."
	@echo "Press Ctrl+C to exit"
	kubectl logs -f -n hubbops -l app=hubbops-backend --tail=50

undeploy: ## Remove Hubbops from K3d
	@echo "🗑️  Removing Hubbops..."
	kubectl delete -f k8s/ingress.yaml --ignore-not-found
	kubectl delete -f k8s/frontend.yaml --ignore-not-found
	kubectl delete -f k8s/backend.yaml --ignore-not-found
	kubectl delete -f k8s/namespace.yaml --ignore-not-found
	@echo "✅ Hubbops removed"

clean: undeploy ## Clean everything including images
	@echo "🧹 Cleaning images..."
	docker rmi $(FRONTEND_IMAGE) $(BACKEND_IMAGE) || true
	@echo "✅ Cleaned"

restart: ## Restart deployments
	@echo "♻️  Restarting deployments..."
	kubectl rollout restart deployment/hubbops-frontend -n hubbops
	kubectl rollout restart deployment/hubbops-backend -n hubbops
	@echo "✅ Deployments restarted"

status: ## Show deployment status
	@echo "📊 Hubbops Status:"
	@echo ""
	@kubectl get all -n hubbops
