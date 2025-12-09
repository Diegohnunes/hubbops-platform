import React, { useState } from 'react';
import { Check, AlertCircle, Code, ArrowLeft } from 'lucide-react';
import './ReviewStep.css';

const ReviewStep = ({ template, formData, onBack, onCreate }) => {
    const [showYaml, setShowYaml] = useState(false);

    // Generate a mock YAML preview (in reality this would come from backend)
    const generateYaml = () => {
        return `apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${formData.service_name || 'my-service'}
  labels:
    app: ${formData.service_name || 'my-service'}
spec:
  replicas: ${formData.replicas || 1}
  selector:
    matchLabels:
      app: ${formData.service_name || 'my-service'}
  template:
    metadata:
      labels:
        app: ${formData.service_name || 'my-service'}
    spec:
      containers:
      - name: ${formData.service_name || 'my-service'}
        image: ${formData.image || 'nginx:latest'}
        ports:
        - containerPort: ${formData.port || 80}
        resources:
          limits:
            cpu: ${formData.cpu_limit || '250m'}
            memory: ${formData.memory_limit || '256Mi'}
---
apiVersion: v1
kind: Service
metadata:
  name: ${formData.service_name || 'my-service'}
spec:
  selector:
    app: ${formData.service_name || 'my-service'}
  ports:
  - port: 80
    targetPort: ${formData.port || 80}
  type: ClusterIP`;
    };

    return (
        <div className="review-step">
            <div className="review-summary">
                <div className="summary-header-row">
                    <div className="summary-header-content">
                        <h2>Service Summary</h2>
                        <span className="template-badge">{template.name}</span>
                    </div>
                </div>

                <div className="summary-grid">
                    {Object.entries(formData).map(([key, value]) => (
                        <div key={key} className="summary-item">
                            <span className="item-label">{key.replace(/_/g, ' ')}</span>
                            <span className="item-value">{String(value)}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="review-preview">
                <div className="preview-header">
                    <div className="preview-tabs">
                        <button
                            className={`tab ${!showYaml ? 'active' : ''}`}
                            onClick={() => setShowYaml(false)}
                        >
                            Summary
                        </button>
                        <button
                            className={`tab ${showYaml ? 'active' : ''}`}
                            onClick={() => setShowYaml(true)}
                        >
                            <Code size={16} />
                            YAML Preview
                        </button>
                    </div>
                </div>

                <div className="preview-content">
                    {!showYaml ? (
                        <div className="preview-info">
                            <div className="info-card success">
                                <Check size={20} />
                                <div>
                                    <strong>Ready to Deploy</strong>
                                    <p>All required fields have been configured</p>
                                </div>
                            </div>

                            <div className="info-card warning">
                                <AlertCircle size={20} />
                                <div>
                                    <strong>Note</strong>
                                    <p>This service will be created in the default namespace</p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <pre className="yaml-preview">
                            <code>{generateYaml()}</code>
                        </pre>
                    )}
                </div>
            </div>

            <div className="review-actions">
                <button className="btn-secondary" onClick={onBack}>
                    Back to Configuration
                </button>
                <button className="btn-primary" onClick={onCreate}>
                    Create Service
                </button>
            </div>
        </div>
    );
};

export default ReviewStep;
