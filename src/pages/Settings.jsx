import React, { useState, useEffect } from 'react';
import { Save, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import './Settings.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function Settings() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const [form, setForm] = useState({
        docker_registry: '',
        git_provider: 'github',
        git_apps_repo: '',
        git_infra_repo: '',
        ssh_private_key: '',
        grafana_enabled: true,
        argocd_enabled: true,
        prometheus_enabled: true
    });

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/config/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();

            if (data.config) {
                setConfig(data);
                setForm({
                    docker_registry: data.config.docker.registry || '',
                    git_provider: data.config.git.provider || 'github',
                    git_apps_repo: data.config.git.apps_configured ? '***' : '', // Can't read actual URL if sensitive, but here we assume we can read from config endpoint if it returns it. The endpoint returns safe dict.
                    // Wait, safe dict returns booleans for repos. We can't edit them if we can't see them.
                    // But for initial setup, they might be empty.
                    // Let's assume the user wants to SET them.
                    git_apps_repo: '',
                    git_infra_repo: '',
                    grafana_enabled: data.config.integrations.grafana.enabled,
                    argocd_enabled: data.config.integrations.argocd.enabled,
                    prometheus_enabled: data.config.integrations.prometheus.enabled
                });
            }
        } catch (err) {
            setError('Failed to load configuration');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setSuccess(null);

        try {
            const token = localStorage.getItem('token');

            // Only send fields that have values (to avoid overwriting with empty strings if not intended)
            const payload = {};
            if (form.docker_registry) payload.docker_registry = form.docker_registry;
            if (form.git_provider) payload.git_provider = form.git_provider;
            if (form.git_apps_repo) payload.git_apps_repo = form.git_apps_repo;
            if (form.git_infra_repo) payload.git_infra_repo = form.git_infra_repo;
            if (form.ssh_private_key) payload.ssh_private_key = form.ssh_private_key;
            payload.grafana_enabled = form.grafana_enabled;
            payload.argocd_enabled = form.argocd_enabled;
            payload.prometheus_enabled = form.prometheus_enabled;

            const res = await fetch(`${API_BASE}/config/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Failed to update configuration');

            const data = await res.json();
            setSuccess('Configuration saved successfully! Please restart the backend to apply changes.');
            fetchConfig();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-8">Loading settings...</div>;

    return (
        <div className="settings-container">
            <div className="settings-header">
                <h1>Platform Settings</h1>
                <p>Configure your HubbOps Platform integrations and defaults.</p>
            </div>

            {error && (
                <div className="alert alert-error">
                    <AlertCircle size={20} />
                    <span>{error}</span>
                </div>
            )}

            {success && (
                <div className="alert alert-success">
                    <CheckCircle size={20} />
                    <span>{success}</span>
                </div>
            )}

            <div className="settings-grid">
                <form onSubmit={handleSubmit} className="settings-form card">
                    <h2>Core Configuration</h2>

                    <div className="form-group">
                        <label>Docker Registry</label>
                        <input
                            type="text"
                            value={form.docker_registry}
                            onChange={e => setForm({ ...form, docker_registry: e.target.value })}
                            placeholder="e.g. docker.io/myuser or local"
                        />
                        <small>Use 'local' for k3d local registry.</small>
                    </div>

                    <div className="form-group">
                        <label>Git Provider</label>
                        <select
                            value={form.git_provider}
                            onChange={e => setForm({ ...form, git_provider: e.target.value })}
                        >
                            <option value="github">GitHub</option>
                            <option value="gitlab">GitLab</option>
                            <option value="bitbucket">Bitbucket</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Apps Repository URL</label>
                        <input
                            type="text"
                            value={form.git_apps_repo}
                            onChange={e => setForm({ ...form, git_apps_repo: e.target.value })}
                            placeholder="git@github.com:user/apps-repo.git"
                        />
                        <small>Where application code will be pushed.</small>
                    </div>

                    <div className="form-group">
                        <label>Infrastructure Repository URL</label>
                        <input
                            type="text"
                            value={form.git_infra_repo}
                            onChange={e => setForm({ ...form, git_infra_repo: e.target.value })}
                            placeholder="git@github.com:user/infra-repo.git"
                        />
                        <small>Where Kubernetes manifests will be pushed (ArgoCD).</small>
                    </div>

                    <div className="form-group">
                        <label>SSH Private Key (Optional)</label>
                        <textarea
                            value={form.ssh_private_key}
                            onChange={e => setForm({ ...form, ssh_private_key: e.target.value })}
                            placeholder="-----BEGIN OPENSSH PRIVATE KEY-----..."
                            rows={5}
                            className="font-mono text-sm"
                        />
                        <small>Private key for accessing the repositories. Stored securely.</small>
                    </div>

                    <h2>Integrations</h2>

                    <div className="checkbox-group">
                        <label>
                            <input
                                type="checkbox"
                                checked={form.grafana_enabled}
                                onChange={e => setForm({ ...form, grafana_enabled: e.target.checked })}
                            />
                            Enable Grafana
                        </label>
                    </div>

                    <div className="checkbox-group">
                        <label>
                            <input
                                type="checkbox"
                                checked={form.argocd_enabled}
                                onChange={e => setForm({ ...form, argocd_enabled: e.target.checked })}
                            />
                            Enable ArgoCD
                        </label>
                    </div>

                    <div className="checkbox-group">
                        <label>
                            <input
                                type="checkbox"
                                checked={form.prometheus_enabled}
                                onChange={e => setForm({ ...form, prometheus_enabled: e.target.checked })}
                            />
                            Enable Prometheus
                        </label>
                    </div>

                    <div className="form-actions">
                        <button type="submit" className="btn-primary" disabled={saving}>
                            {saving ? <RefreshCw className="spin" /> : <Save />}
                            Save Changes
                        </button>
                    </div>
                </form>

                <div className="status-card card">
                    <h2>Current Status</h2>
                    <div className="status-list">
                        <div className="status-item">
                            <span>Docker Registry</span>
                            <span className="badge">{config?.config?.docker?.registry}</span>
                        </div>
                        <div className="status-item">
                            <span>Apps Repo</span>
                            <span className={`badge ${config?.config?.git?.apps_configured ? 'success' : 'warning'}`}>
                                {config?.config?.git?.apps_configured ? 'Configured' : 'Missing'}
                            </span>
                        </div>
                        <div className="status-item">
                            <span>Infra Repo</span>
                            <span className={`badge ${config?.config?.git?.infra_configured ? 'success' : 'warning'}`}>
                                {config?.config?.git?.infra_configured ? 'Configured' : 'Missing'}
                            </span>
                        </div>
                    </div>

                    <h3>Integration Health</h3>
                    <div className="status-list">
                        {Object.entries(config?.integrations || {}).map(([key, val]) => (
                            <div key={key} className="status-item">
                                <span className="capitalize">{key}</span>
                                <span className={`badge ${val.status === 'connected' ? 'success' : 'error'}`}>
                                    {val.status}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Settings;
