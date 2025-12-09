#!/bin/bash
# ============================================================
# K3d Cluster Setup with Registry for Kaniko
# ============================================================
# This script creates a K3d cluster with a local registry
# that Kaniko can push images to.
# ============================================================

set -e

CLUSTER_NAME="${CLUSTER_NAME:-devlab}"
REGISTRY_NAME="${REGISTRY_NAME:-k3d-${CLUSTER_NAME}-registry}"
REGISTRY_PORT="${REGISTRY_PORT:-5000}"

echo "============================================================"
echo " K3d Cluster Setup with Registry"
echo "============================================================"
echo ""
echo " Cluster: $CLUSTER_NAME"
echo " Registry: $REGISTRY_NAME:$REGISTRY_PORT"
echo ""

# Check if cluster already exists
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo "⚠️  Cluster '$CLUSTER_NAME' already exists."
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing cluster..."
        k3d cluster delete "$CLUSTER_NAME"
    else
        echo "Aborting."
        exit 1
    fi
fi

echo ""
echo "Step 1/3: Creating cluster with registry..."
echo "============================================================"

# Create cluster with:
# - Local registry for Kaniko to push images to
# - Port mappings for frontend (80) and backend (8000)
k3d cluster create "$CLUSTER_NAME" \
    --registry-create "$REGISTRY_NAME:$REGISTRY_PORT" \
    -p "8080:80@loadbalancer" \
    -p "8443:443@loadbalancer" \
    --agents 0 \
    --wait

echo ""
echo "Step 2/3: Verifying cluster..."
echo "============================================================"

# Wait for cluster to be ready
kubectl wait --for=condition=Ready nodes --all --timeout=120s

echo "✅ Cluster nodes are ready"

# Verify registry
echo ""
echo "Registry URL: $REGISTRY_NAME:$REGISTRY_PORT"
echo "From inside K3d: k3d-$CLUSTER_NAME-registry:$REGISTRY_PORT"

echo ""
echo "Step 3/3: Setup complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Build and import HubbOps images:"
echo "     docker build -f Dockerfile.backend -t hubbops-backend:latest ."
echo "     docker build -f Dockerfile.frontend -t hubbops-frontend:latest ."
echo "     k3d image import hubbops-backend:latest hubbops-frontend:latest -c $CLUSTER_NAME"
echo ""
echo "  2. Deploy HubbOps:"
echo "     kubectl apply -f k8s/namespace.yaml"
echo "     kubectl apply -f k8s/pvc.yaml"
echo "     kubectl apply -f k8s/kaniko-rbac.yaml"
echo "     kubectl apply -f k8s/backend.yaml"
echo "     kubectl apply -f k8s/frontend.yaml"
echo ""
echo "  3. Deploy your observability stack from your external repo"
echo ""
echo "  4. Access HubbOps:"
echo "     kubectl port-forward -n hubbops svc/hubbops-frontend 8080:80"
echo "     Open http://localhost:8080"
echo ""
echo "============================================================"
echo "✅ K3d cluster '$CLUSTER_NAME' is ready!"
echo "============================================================"
