# User Guide

Welcome to the HubbOps Platform! This guide covers the basics of using the platform.

## Getting Started

### Login

Access the platform at `http://localhost:3000` (or your deployed URL).
-   If this is the first time, you will be prompted to create an **Admin** account.
-   Otherwise, log in with your email and password.

## Managing Services

### Creating a Service

1.  Navigate to the **Create Service** page.
2.  Select a **Template** (e.g., Python Service, Go Service).
3.  Fill in the required fields:
    -   **Service Name**: Unique name for your service (e.g., `my-api`).
    -   **Port**: The port your application listens on.
    -   **Resources**: CPU/Memory limits.
4.  Click **Create Service**.
5.  Watch the **Real-time Logs** to see the creation process (Code generation -> Docker build -> Git push).

### Viewing Services

-   Go to the **Services** page to see a list of all running services.
-   Click on a service to view details, including:
    -   Status (Running, Failed, etc.)
    -   Links to Source Code and ArgoCD.
    -   Recent logs.

### Deleting a Service

1.  Go to the Service Details page.
2.  Click the **Delete** button (requires Admin or Developer role).
3.  Confirm the deletion. This will remove the service from Kubernetes and delete the ArgoCD application.

## User Management (Admin Only)

### Managing Users

1.  Navigate to the **Users & Groups** page.
2.  You will see a list of registered users.
3.  (Future) You can add new users, change roles, or deactivate accounts.

### Roles

-   **Admin**: Can do everything (manage users, services, system config).
-   **Developer**: Can create, update, and delete services.
-   **Viewer**: Can only view services and dashboards.

## Troubleshooting

### Service Creation Failed

-   Check the **Real-time Logs** in the creation modal.
-   Common errors:
    -   **Git Error**: Check your Git credentials in `config/secrets.yaml`.
    -   **Docker Error**: Ensure Docker is running and the registry is accessible.
    -   **Validation Error**: Check that your service name contains only alphanumeric characters.

### Deployment Issues

-   Check **ArgoCD** to see if the application is syncing correctly.
-   Use `kubectl get pods -n <service-name>` to check the pod status.
