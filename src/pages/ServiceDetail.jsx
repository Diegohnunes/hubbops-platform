import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Pause, Trash2, AlertCircle, Pencil } from 'lucide-react';
import { apiClient } from '../utils/api';
import './ServiceDetail.css';

const ServiceDetail = () => {
    const { serviceId } = useParams();
    const navigate = useNavigate();
    const [service, setService] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        loadService();
    }, [serviceId]);

    const loadService = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await apiClient.getService(serviceId);
            setService(data);
        } catch (err) {
            setError(err.message || 'Failed to load service');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleStatus = async () => {
        if (!service) return;

        try {
            setActionLoading(true);
            const isActive = service.status === 'active' || service.status === 'running';

            if (isActive) {
                await apiClient.stopService(serviceId);
                setService({ ...service, status: 'inactive' });
            } else {
                await apiClient.startService(serviceId);
                setService({ ...service, status: 'active' });
            }
        } catch (err) {
            alert(`Failed to ${service.status === 'active' ? 'deactivate' : 'activate'} service: ${err.message}`);
        } finally {
            setActionLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!service) return;

        const confirmed = window.confirm(
            `Are you sure you want to delete "${service.name}"? This action cannot be undone.`
        );

        if (!confirmed) return;

        try {
            setActionLoading(true);
            await apiClient.deleteService(serviceId);
            navigate('/services');
        } catch (err) {
            alert(`Failed to delete service: ${err.message}`);
            setActionLoading(false);
        }
    };

    const getStatusColor = (status) => {
        const colors = {
            creating: 'status-creating',
            active: 'status-running',
            running: 'status-running',
            inactive: 'status-stopped',
            failed: 'status-failed'
        };
        return colors[status] || 'status-unknown';
    };

    if (loading) {
        return (
            <div className="service-detail-page">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading service details...</p>
                </div>
            </div>
        );
    }

    if (error || !service) {
        return (
            <div className="service-detail-page">
                <div className="error-state">
                    <AlertCircle size={64} />
                    <h2>Error Loading Service</h2>
                    <p>{error || 'Service not found'}</p>
                    <button className="btn-primary" onClick={() => navigate('/services')}>
                        Back to Services
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="service-detail-page">
            <div className="detail-header">
                <button className="btn-back" onClick={() => navigate('/services')}>
                    <ArrowLeft size={20} />
                    Back to Services
                </button>

                <div className="detail-title">
                    <h1>{service.name}</h1>
                    <span className={`status-badge ${getStatusColor(service.status)}`}>
                        {service.status}
                    </span>
                </div>

                <div className="detail-actions">
                    <button
                        className="btn-secondary"
                        onClick={handleToggleStatus}
                        disabled={actionLoading || service.status === 'creating'}
                    >
                        {service.status === 'active' || service.status === 'running' ? (
                            <>
                                <Pause size={16} />
                                Deactivate
                            </>
                        ) : (
                            <>
                                <Play size={16} />
                                Activate
                            </>
                        )}
                    </button>
                    <button
                        className="btn-secondary"
                        onClick={() => navigate(`/services/${serviceId}/edit`)}
                        disabled={actionLoading}
                    >
                        <Pencil size={16} />
                        Edit
                    </button>
                    <button
                        className="btn-danger"
                        onClick={handleDelete}
                        disabled={actionLoading}
                    >
                        <Trash2 size={16} />
                        Delete
                    </button>
                </div>
            </div>

            <div className="detail-grid">
                <div className="detail-card">
                    <h3>Service Information</h3>
                    <div className="detail-info">
                        <div className="info-row">
                            <span className="info-label">Service ID</span>
                            <span className="info-value">{service.id}</span>
                        </div>
                        <div className="info-row">
                            <span className="info-label">Template</span>
                            <span className="info-value">{service.template}</span>
                        </div>
                        <div className="info-row">
                            <span className="info-label">Namespace</span>
                            <span className="info-value">{service.namespace}</span>
                        </div>
                        <div className="info-row">
                            <span className="info-label">Created At</span>
                            <span className="info-value">
                                {new Date(service.created_at).toLocaleString()}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="detail-card">
                    <h3>Configuration</h3>
                    <div className="detail-info">
                        <pre className="config-json">
                            {JSON.stringify(service.config || {}, null, 2)}
                        </pre>
                    </div>
                </div>

                <div className="detail-card full-width">
                    <h3>Quick Links</h3>
                    <div className="quick-links">
                        <a href="#" className="link-card">
                            <div className="link-icon">📊</div>
                            <div className="link-content">
                                <h4>Grafana Dashboard</h4>
                                <p>View metrics and performance</p>
                            </div>
                        </a>
                        <a href="#" className="link-card">
                            <div className="link-icon">🔄</div>
                            <div className="link-content">
                                <h4>ArgoCD</h4>
                                <p>Deployment status</p>
                            </div>
                        </a>
                        <a href="#" className="link-card">
                            <div className="link-icon">📝</div>
                            <div className="link-content">
                                <h4>Logs</h4>
                                <p>View service logs</p>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ServiceDetail;
