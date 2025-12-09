import React from 'react';
import './Documentation.css';

const Documentation = () => {
    return (
        <div className="documentation-page">
            <div className="docs-header">
                <h1>Documentation</h1>
                <p className="docs-subtitle">
                    Learn how to use Hubbops to create and manage infrastructure
                </p>
            </div>

            <div className="docs-grid">
                <div className="docs-card">
                    <div className="docs-icon primary">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                            <path d="M2 17l10 5 10-5"></path>
                            <path d="M2 12l10 5 10-5"></path>
                        </svg>
                    </div>
                    <h2>Getting Started</h2>
                    <p>Hubbops is an Internal Developer Platform that simplifies infrastructure management. Create services, databases, and cloud resources with just a few clicks.</p>
                    <ul>
                        <li>Self-service infrastructure provisioning</li>
                        <li>40+ templates (10 ready, 30+ coming soon)</li>
                        <li>Kubernetes-native with K3d support</li>
                        <li>Premium UI with dark/light themes</li>
                    </ul>
                </div>

                <div className="docs-card">
                    <div className="docs-icon success">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </div>
                    <h2>Creating Services</h2>
                    <p>Follow these steps to create your first service:</p>
                    <ol>
                        <li>Navigate to "Create Service" in the sidebar</li>
                        <li>Choose a template (Python, Go, Frontend, Database, etc.)</li>
                        <li>Fill in the configuration form</li>
                        <li>Review the generated YAML/JSON</li>
                        <li>Click "Create Service" to deploy</li>
                    </ol>
                </div>

                <div className="docs-card">
                    <div className="docs-icon info">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="9" y1="9" x2="15" y2="9"></line>
                            <line x1="9" y1="15" x2="15" y2="15"></line>
                        </svg>
                    </div>
                    <h2>Available Templates</h2>
                    <h3>Ready Now (✅)</h3>
                    <ul>
                        <li><strong>Simple Service</strong> - Basic Kubernetes deployment</li>
                        <li><strong>Python Service</strong> - Python + Gunicorn</li>
                        <li><strong>Go Service</strong> - Optimized Go app</li>
                        <li><strong>Frontend App</strong> - React/Vue/Next.js</li>
                        <li><strong>PostgreSQL</strong> - Database with PVC</li>
                        <li><strong>Redis</strong> - Cache & message broker</li>
                    </ul>
                    <h3>Coming Soon (🔜)</h3>
                    <ul>
                        <li>AWS resources (S3, Lambda, EC2, RDS)</li>
                        <li>GCP & Azure resources</li>
                        <li>MongoDB, Elasticsearch, Kafka</li>
                        <li>ML/AI tools (Jupyter, MLflow)</li>
                        <li>CI/CD runners (Jenkins, GitHub Actions)</li>
                    </ul>
                </div>

                <div className="docs-card">
                    <div className="docs-icon warning">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 6v4"></path>
                            <path d="M12 14h.01"></path>
                        </svg>
                    </div>
                    <h2>Architecture</h2>
                    <p>Hubbops is built with:</p>
                    <ul>
                        <li><strong>Frontend</strong>: React + Vite + TailwindCSS</li>
                        <li><strong>Backend</strong>: FastAPI (Python) - planned</li>
                        <li><strong>Orchestration</strong>: Kubernetes (K3d)</li>
                        <li><strong>GitOps</strong>: ArgoCD for deployments</li>
                        <li><strong>Monitoring</strong>: Grafana dashboards</li>
                        <li><strong>IaC</strong>: Terraform for cloud resources</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default Documentation;
