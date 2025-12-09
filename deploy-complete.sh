#!/bin/bash
# Complete deployment script with Docker fix and ArgoCD

set -e

echo "🚀 Complete Hubbops Deployment"
echo "==============================="
echo ""

# Step 1: Fix Docker credentials
echo "🔧 Step 1/4: Fixing Docker credentials..."
if [ -f ~/.docker/config.json ]; then
    cp ~/.docker/config.json ~/.docker/config.json.backup.$(date +%s) 2>/dev/null || true
fi

mkdir -p ~/.docker
cat > ~/.docker/config.json << 'EOF'
{
  "auths": {}
}
EOF

echo "✅ Docker config fixed"
echo ""

# Step 2: Build images
echo "🔨 Step 2/4: Building images..."
cd /home/diego/crypto-plataform/hubbops-platform
docker build -f Dockerfile.frontend -t hubbops-frontend:latest . || {
    echo "❌ Frontend build failed"
    exit 1
}

docker build -f Dockerfile.backend -t hubbops-backend:latest . || {
    echo "❌ Backend build failed"
    exit 1
}
echo "✅ Images built"
echo ""

# Step 3: Import to K3d and restart
echo "📥 Step 3/4: Importing to K3d..."
k3d image import hubbops-frontend:latest -c devlab
k3d image import hubbops-backend:latest -c devlab

echo "🔄 Restarting deployments..."
kubectl rollout restart deployment/hubbops-frontend -n hubbops
kubectl rollout restart deployment/hubbops-backend -n hubbops
echo "✅ Deployments restarted"
echo ""

# Step 4: Recreate ArgoCD frontend if needed
echo "🔄 Step 4/4: Checking ArgoCD Applications..."
if ! kubectl get application crypto-frontend -n argocd &>/dev/null; then
    echo "📝 Recreating crypto-frontend ArgoCD Application..."
    kubectl apply -f /home/diego/crypto-plataform/infraestrutura-hubbops-plataform/gitops/apps/crypto-frontend.yaml
    echo "✅ ArgoCD Application recreated"
else
    echo "✅ ArgoCD Application already exists"
fi

echo ""
echo "⏳ Waiting for pods..."
kubectl wait --for=condition=ready pod -l app=hubbops-backend -n hubbops --timeout=120s 2>/dev/null || echo "⚠️  Backend pods may take longer"
kubectl wait --for=condition=ready pod -l app=hubbops-frontend -n hubbops --timeout=120s 2>/dev/null || echo "⚠️  Frontend pods may take longer"

echo ""
echo "🔄 Running Database Migration..."
kubectl exec -n hubbops deployment/hubbops-backend -- python3 migrate_db.py || echo "⚠️  Migration failed (or script not found)"

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 Pod Status:"
kubectl get pods -n hubbops
echo ""
echo "📊 ArgoCD Applications:"
kubectl get applications -n argocd | grep crypto
echo ""
echo "🌐 Access: make port-forward"
