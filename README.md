# HubbOps Platform

**An Open Source Internal Developer Platform (IDP)**

HubbOps is a modern, extensible IDP designed to automate the creation, deployment, and management of microservices on Kubernetes. It provides a self-service portal for developers to spin up new services in minutes, complete with CI/CD, monitoring, and GitOps best practices.

![HubbOps Dashboard](https://via.placeholder.com/800x400?text=HubbOps+Dashboard+Preview)

## 🚀 Features

-   **Self-Service Portal**: Create services (Python, Go, etc.) via a user-friendly wizard.
-   **GitOps Native**: Everything is code. Changes are pushed to Git and synced via ArgoCD.
-   **Automated Infrastructure**: Generates Dockerfiles, K8s manifests, and Helm charts automatically.
-   **Built-in Monitoring**: Automatic Grafana dashboards and Prometheus metrics for every service.
-   **Role-Based Access Control (RBAC)**: Secure access for Admins, Developers, and Viewers.
-   **Extensible Architecture**: Easy to add new service templates and infrastructure components.

## 📚 Documentation

-   [**Setup Guide**](docs/SETUP.md): How to install and run HubbOps locally.
-   [**Architecture**](docs/ARCHITECTURE.md): Deep dive into the system components and data flow.
-   [**User Guide**](docs/USER_GUIDE.md): How to use the platform to manage services.
-   [**Contributing**](CONTRIBUTING.md): How to contribute to the project.

## 🛠️ Quick Start

HubbOps can run on **any Kubernetes cluster** (Local or Cloud).

### 1. Clone the repo
```bash
git clone https://github.com/Diegohnunes/hubbops-platform.git
cd hubbops-platform
```

### 2. Configure
```bash
cp config/settings.example.yaml config/settings.yaml
# Edit config/settings.yaml with your Docker/Git details
```

### 3. Deploy
Choose your environment:

*   **Production / Cloud**: `kubectl apply -f k8s/`
*   **Local (k3d/minikube)**: See [Setup Guide](docs/SETUP.md) for local cluster scripts.

> 📘 Full detailed instructions in [**Setup Guide**](docs/SETUP.md).

4.  **Access**:
    -   Frontend: `http://localhost:3000`
    -   Backend API: `http://localhost:8000`

## 🏗️ Tech Stack

-   **Frontend**: React, Vite, Tailwind-like CSS
-   **Backend**: Python, FastAPI, SQLModel
-   **Automation**: Python CLI, Jinja2
-   **Infrastructure**: Kubernetes (k3d), ArgoCD, Prometheus, Grafana

## 📄 License

This project is licensed under the [MIT License](LICENSE).
