# Setup Guide

This guide covers how to set up HubbOps in different environments.

## Prerequisites

| Tool | Required | Notes |
|------|----------|-------|
| **Docker** | ✅ Yes | Container runtime |
| **kubectl** | ✅ Yes | Kubernetes CLI |
| **Python 3.11+** | ✅ Yes | Backend and CLI |
| **Node.js 18+** | ✅ Yes | Frontend build |
| **Git** | ✅ Yes | GitOps workflow |
| **k3d / minikube** | Only for local | Local K8s cluster |
| **Helm** | Optional | Package management |
| **ArgoCD** | ✅ Yes | GitOps controller |

---

## Quick Start (TL;DR)

```bash
# Clone
git clone https://github.com/Diegohnunes/hubbops-platform.git
cd hubbops-platform

# Configure
cp config/settings.example.yaml config/settings.yaml
# Edit config/settings.yaml with your Git repos and registry

# Deploy to your cluster
kubectl apply -f k8s/

# Access
kubectl port-forward -n hubbops svc/hubbops-frontend 8080:80
# Open http://localhost:8080
```

---

## Deployment Scenarios

### Scenario A: Existing Kubernetes Cluster (Production)

If you already have a running K8s cluster (EKS, GKE, AKS, on-prem), follow these steps:

#### 1. Push Images to Your Registry

```bash
# Build
docker build -f Dockerfile.backend -t <YOUR_REGISTRY>/hubbops-backend:latest .
docker build -f Dockerfile.frontend -t <YOUR_REGISTRY>/hubbops-frontend:latest .

# Push
docker push <YOUR_REGISTRY>/hubbops-backend:latest
docker push <YOUR_REGISTRY>/hubbops-frontend:latest
```

#### 2. Update Manifests

Edit `k8s/backend.yaml` and `k8s/frontend.yaml` to use your registry:

```yaml
# k8s/backend.yaml
containers:
  - name: hubbops-backend
    image: <YOUR_REGISTRY>/hubbops-backend:latest  # <-- Change this
```

#### 3. Deploy

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml  # Optional: configure for your ingress controller
```

#### 4. Configure ArgoCD

HubbOps requires ArgoCD to be installed in your cluster:

```bash
# Install ArgoCD (if not already installed)
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Add your Git repository with SSH key
argocd repo add git@github.com:YourOrg/your-infra-repo.git --ssh-private-key-path ~/.ssh/id_rsa
```

---

### Scenario B: Local Development (k3d)

Best for testing and development on your local machine.

#### 1. Create Cluster

```bash
k3d cluster create devlab --api-port 6550 -p "8080:80@loadbalancer" --agents 1
```

#### 2. Build and Import Images

```bash
# Build
docker build -f Dockerfile.backend -t hubbops-backend:latest .
docker build -f Dockerfile.frontend -t hubbops-frontend:latest .

# Import to k3d (no registry needed)
k3d image import hubbops-backend:latest -c devlab
k3d image import hubbops-frontend:latest -c devlab
```

#### 3. Deploy

```bash
kubectl apply -f k8s/
```

#### 4. Access

```bash
kubectl port-forward -n hubbops svc/hubbops-frontend 8080:80 &
kubectl port-forward -n hubbops svc/hubbops-backend 8000:8000 &
# Open http://localhost:8080
```

---

### Scenario C: Local Development (minikube)

#### 1. Create Cluster

```bash
minikube start --cpus 4 --memory 8192
```

#### 2. Build Images (using minikube's Docker)

```bash
eval $(minikube docker-env)
docker build -f Dockerfile.backend -t hubbops-backend:latest .
docker build -f Dockerfile.frontend -t hubbops-frontend:latest .
```

#### 3. Deploy

```bash
kubectl apply -f k8s/
```

#### 4. Access

```bash
minikube service hubbops-frontend -n hubbops
```

---

## Configuration

### Settings File

Copy and edit `config/settings.yaml`:

```yaml
git:
  repositories:
    infrastructure:
      url: "git@github.com:YourOrg/your-infra-repo.git"  # SSH URL for private repos
    applications:
      url: "git@github.com:YourOrg/your-apps-repo.git"

docker:
  registry: "your-registry.io"  # Or "local" for k3d/minikube
  k3d_cluster: "devlab"         # Leave empty if not using k3d
```

### SSH Key for Private Repos

For GitOps with private repositories:

1. Go to **Settings** in the HubbOps UI.
2. Paste your SSH private key.
3. Click **Save**.

The key will be used for Git operations (clone, push).

---

## First-Time Setup

1. Open HubbOps at `http://localhost:8080`.
2. Create an **Admin** account.
3. Go to **Settings** and configure:
   - Git Repository URLs (use SSH format: `git@github.com:...`)
   - SSH Private Key (for private repos)
4. Create your first service!

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **401 Unauthorized** | Clear browser cache and re-login |
| **ArgoCD sync failed** | Check ArgoCD has access to your Git repo (SSH key) |
| **Image pull error** | Ensure images are pushed to your registry |
| **Service not deploying** | Check `kubectl logs -n <namespace> <pod>` |

---

## Next Steps

- Read the [User Guide](USER_GUIDE.md) for detailed usage instructions.
- Check the [Architecture](ARCHITECTURE.md) to understand the system design.
