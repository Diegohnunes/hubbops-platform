import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle, FileCode, Terminal, XCircle, Loader } from 'lucide-react';

const ReviewCard = ({ template, formData, onBack, onCreate }) => {
    const [status, setStatus] = useState('idle'); // idle, creating, success, error
    const [logs, setLogs] = useState([]);
    const logsEndRef = useRef(null);

    const scrollToBottom = () => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [logs]);

    const addLog = (message, type = 'info') => {
        setLogs(prev => [...prev, { timestamp: new Date().toISOString().split('T')[1].split('.')[0], message, type }]);
    };

    const handleCreate = async () => {
        setStatus('creating');
        setLogs([]);

        const steps = [
            { msg: "Initializing deployment workflow...", delay: 500 },
            { msg: `Validating configuration for ${formData.serviceName}...`, delay: 1000 },
            { msg: "Generating Kubernetes manifests...", delay: 800 },
            { msg: "Generating Helm release values...", delay: 600 },
            { msg: "Committing changes to GitOps repository...", delay: 1500 },
            { msg: "Pushing to branch 'feature/new-service'...", delay: 1200 },
            { msg: "Creating Pull Request...", delay: 1000 },
            { msg: "Waiting for CI checks...", delay: 2000 },
            { msg: "CI checks passed.", type: "success", delay: 500 },
            { msg: "Merging Pull Request...", delay: 1000 },
            { msg: "Syncing with ArgoCD...", delay: 1500 },
            { msg: "Deployment triggered successfully!", type: "success", delay: 500 },
        ];

        for (const step of steps) {
            await new Promise(resolve => setTimeout(resolve, step.delay));
            addLog(step.msg, step.type || 'info');
        }

        setStatus('success');
        if (onCreate) onCreate();
    };

    if (status === 'success') {
        return (
            <div className="animate-fade-in flex flex-col items-center justify-center py-12 text-center">
                <div className="w-16 h-16 bg-success/20 text-success rounded-full flex items-center justify-center mb-6" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: 'var(--success)' }}>
                    <CheckCircle size={32} />
                </div>
                <h2 className="text-2xl font-bold mb-2">Service Created Successfully!</h2>
                <p className="text-secondary mb-8 max-w-md" style={{ color: 'var(--text-secondary)' }}>
                    Your service <strong>{formData.serviceName}</strong> has been provisioned and is now deploying to the <strong>{formData.environment?.[0] || 'dev'}</strong> environment.
                </p>

                {/* Logs Summary */}
                <div className="w-full max-w-2xl bg-black/80 rounded-lg p-4 mb-8 text-left font-mono text-xs h-48 overflow-auto border border-border" style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)', borderColor: 'var(--border-color)' }}>
                    {logs.map((log, i) => (
                        <div key={i} className={`${log.type === 'success' ? 'text-green-400' : 'text-gray-300'}`}>
                            <span className="text-gray-500 mr-2">[{log.timestamp}]</span>
                            {log.message}
                        </div>
                    ))}
                </div>

                <div className="flex gap-4">
                    <button className="btn border border-border text-secondary hover:text-primary" style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
                        View Full Logs
                    </button>
                    <button className="btn btn-primary" style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                        Go to Service Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="animate-fade-in max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">Review & Confirm</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Summary */}
                <div className="space-y-6">
                    <div className="card" style={{ backgroundColor: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <template.icon size={20} className={template.color} />
                            {template.name}
                        </h3>

                        <dl className="space-y-4">
                            <div className="flex justify-between border-b border-border pb-2" style={{ borderBottom: '1px solid var(--border-color)' }}>
                                <dt className="text-secondary" style={{ color: 'var(--text-secondary)' }}>Service Name</dt>
                                <dd className="font-medium text-right">{formData.serviceName}</dd>
                            </div>
                            <div className="flex justify-between border-b border-border pb-2" style={{ borderBottom: '1px solid var(--border-color)' }}>
                                <dt className="text-secondary" style={{ color: 'var(--text-secondary)' }}>Owner</dt>
                                <dd className="font-medium text-right">{formData.owner}</dd>
                            </div>
                            <div className="flex justify-between border-b border-border pb-2" style={{ borderBottom: '1px solid var(--border-color)' }}>
                                <dt className="text-secondary" style={{ color: 'var(--text-secondary)' }}>Environments</dt>
                                <dd className="font-medium text-right flex gap-1 justify-end">
                                    {formData.environment?.map(env => (
                                        <span key={env} className="text-xs bg-tertiary px-2 py-1 rounded uppercase" style={{ backgroundColor: 'var(--bg-tertiary)' }}>{env}</span>
                                    ))}
                                </dd>
                            </div>
                        </dl>
                    </div>

                    {/* Terminal / Logs Area */}
                    {status === 'creating' ? (
                        <div className="bg-black rounded-lg p-4 font-mono text-xs overflow-hidden border border-border h-64 flex flex-col" style={{ backgroundColor: '#000', borderColor: 'var(--border-color)' }}>
                            <div className="flex items-center gap-2 text-gray-400 mb-2 border-b border-gray-800 pb-2">
                                <Loader size={14} className="animate-spin" />
                                <span>Deployment in progress...</span>
                            </div>
                            <div className="flex-1 overflow-auto space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className={`${log.type === 'success' ? 'text-green-400' : 'text-gray-300'}`}>
                                        <span className="text-gray-600 mr-2">[{log.timestamp}]</span>
                                        {log.message}
                                    </div>
                                ))}
                                <div ref={logsEndRef} />
                            </div>
                        </div>
                    ) : (
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 text-sm text-blue-200" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.2)', color: '#bfdbfe' }}>
                            <p className="flex gap-2">
                                <Terminal size={16} className="mt-0.5" />
                                This will trigger a GitOps workflow. A pull request will be automatically created and merged to apply these changes.
                            </p>
                        </div>
                    )}
                </div>

                {/* Code Preview */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-bold flex items-center gap-2">
                            <FileCode size={18} />
                            Generated Manifest
                        </h3>
                        <span className="text-xs text-secondary" style={{ color: 'var(--text-secondary)' }}>preview.yaml</span>
                    </div>

                    <div className="bg-black/50 rounded-lg p-4 font-mono text-xs overflow-auto h-96 border border-border" style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)', borderColor: 'var(--border-color)' }}>
                        <pre className="text-gray-300">
                            {`apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: ${formData.serviceName}
  description: ${formData.description}
  annotations:
    github.com/project-slug: ${formData.owner}/${formData.serviceName}
spec:
  type: service
  lifecycle: production
  owner: ${formData.owner}
  system: crypto-platform
  dependsOn:
    - resource:default/postgres-db
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: ${formData.serviceName}
spec:
  values:
    image:
      repository: ${formData.image || 'nginx'}
      tag: latest
    resources:
      limits:
        cpu: ${formData.cpu_limit || '100m'}
        memory: ${formData.memory_limit || '128Mi'}
    ingress:
      enabled: ${formData.ingress ? 'true' : 'false'}
`}
                        </pre>
                    </div>
                </div>
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button
                    onClick={onBack}
                    className="btn text-secondary hover:text-primary"
                    style={{ color: 'var(--text-secondary)' }}
                    disabled={status === 'creating'}
                >
                    Back
                </button>
                <button
                    onClick={handleCreate}
                    className="btn btn-primary px-8 flex items-center gap-2"
                    style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}
                    disabled={status === 'creating'}
                >
                    {status === 'creating' ? (
                        <>
                            <span className="animate-spin">⏳</span> Deploying...
                        </>
                    ) : (
                        'Create Service'
                    )}
                </button>
            </div>
        </div>
    );
};

export default ReviewCard;
