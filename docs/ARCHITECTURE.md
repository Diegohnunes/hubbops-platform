# System Architecture

HubbOps is designed as a modular Internal Developer Platform (IDP) that automates the creation and deployment of microservices.

## High-Level Overview

```mermaid
graph TD
    User[User] -->|Browser| Frontend[Frontend (React)]
    Frontend -->|REST API| Backend[Backend (FastAPI)]
    Backend -->|Database| SQLite[(SQLite DB)]
    Backend -->|Executes| CLI[Ops-CLI (Python)]
    CLI -->|Generates Code| AppsRepo[Git: Apps Repo]
    CLI -->|Generates Manifests| InfraRepo[Git: Infra Repo]
    CLI -->|Builds| Docker[Docker Registry]
    
    subgraph Kubernetes Cluster
        ArgoCD[ArgoCD]
        App[Deployed App]
        Prometheus[Prometheus]
        Grafana[Grafana]
    end
    
    ArgoCD -->|Watches| InfraRepo
    ArgoCD -->|Deploys| App
    Prometheus -->|Scrapes| App
    Grafana -->|Visualizes| Prometheus
```

## Components

### 1. Frontend (`/src`)
-   **Tech**: React, Vite, Lucide Icons.
-   **Role**: User interface for the platform.
-   **Features**:
    -   Service creation wizard (dynamic forms based on templates).
    -   Service catalog and details.
    -   User and group management.
    -   Real-time logs (WebSockets).

### 2. Backend (`/backend`)
-   **Tech**: Python, FastAPI, SQLModel (SQLite), AsyncIO.
-   **Role**: API gateway and orchestrator.
-   **Features**:
    -   **Auth**: JWT-based authentication and RBAC.
    -   **Process Manager**: Runs background tasks (CLI commands) and streams logs.
    -   **Config**: Centralized configuration management.

### 3. Ops-CLI (`/ops-cli`)
-   **Tech**: Python, Jinja2, Click (or argparse).
-   **Role**: The automation engine.
-   **Features**:
    -   **Handlers**: Logic for different service types (Python, Go, etc.).
    -   **Templates**: Jinja2 templates for code and manifests.
    -   **GitOps**: Handles cloning, committing, and pushing to Git repositories.

### 4. Infrastructure (`/k8s`, `/gitops`)
-   **Tech**: Kubernetes, ArgoCD, Prometheus, Grafana.
-   **Role**: Runtime environment.
-   **Workflow**:
    1.  **Code Generation**: CLI generates app code and K8s manifests.
    2.  **Git Push**: Code goes to Apps Repo, Manifests go to Infra Repo.
    3.  **Sync**: ArgoCD detects changes in Infra Repo and applies them to the cluster.

## Data Flow: Service Creation

1.  **Form Submission**: User fills out a form in the Frontend.
2.  **API Request**: Frontend sends a JSON payload to `POST /api/services`.
3.  **Record Creation**: Backend creates a `Service` record with status `creating`.
4.  **CLI Execution**: Backend spawns a background process running `ops-cli create`.
5.  **Handler Execution**:
    -   `ops-cli` loads the appropriate handler (e.g., `PythonServiceHandler`).
    -   Validates configuration.
    -   Generates code from templates.
    -   Generates K8s manifests.
    -   Builds and pushes Docker image.
    -   Commits and pushes to Git.
6.  **Deployment**: ArgoCD syncs the new application.
7.  **Completion**: Backend updates service status to `active`.

## Authentication

-   **Model**: JWT (JSON Web Tokens).
-   **Storage**: SQLite (Users, Groups, Sessions).
-   **Hashing**: bcrypt (via passlib).
-   **RBAC**:
    -   **Admin**: Full access.
    -   **Developer**: Can create/edit services.
    -   **Viewer**: Read-only access.
