import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Package, Search, Filter, Play, Pause } from 'lucide-react';
import { apiClient } from '../utils/api';
import './Services.css';

const Services = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
    const [filteredServices, setFilteredServices] = useState([]);
    const [actionLoading, setActionLoading] = useState(null); // Track which service is being modified

    useEffect(() => {
        loadServices();
    }, []);

    useEffect(() => {
        // Filter services based on search query
        if (searchQuery.trim()) {
            const filtered = services.filter(service =>
                service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                service.template.toLowerCase().includes(searchQuery.toLowerCase()) ||
                service.namespace.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setFilteredServices(filtered);
        } else {
            setFilteredServices(services);
        }
    }, [searchQuery, services]);

    const loadServices = async () => {
        try {
            setLoading(true);
            const data = await apiClient.listServices();
            setServices(data.services || []);
        } catch (error) {
            console.error('Failed to load services:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async (serviceId, serviceName, event) => {
        event.stopPropagation();
        if (!window.confirm(`Are you sure you want to stop "${serviceName}"?`)) return;

        try {
            setActionLoading(serviceId);
            await apiClient.stopService(serviceId);
            await loadServices();
        } catch (error) {
            alert(`Failed to stop service: ${error.message}`);
        } finally {
            setActionLoading(null);
        }
    };

    const handleStart = async (serviceId, serviceName, event) => {
        event.stopPropagation();
        try {
            setActionLoading(serviceId);
            await apiClient.startService(serviceId);
            await loadServices();
        } catch (error) {
            alert(`Failed to start service: ${error.message}`);
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async (serviceId, serviceName, event) => {
        event.stopPropagation(); // Prevent navigation when clicking delete

        const confirmed = window.confirm(
            `Are you sure you want to delete "${serviceName}"? This action cannot be undone.`
        );

        if (!confirmed) return;

        try {
            await apiClient.deleteService(serviceId);
            // Reload services after deletion
            loadServices();
        } catch (error) {
            alert(`Failed to delete service: ${error.message}`);
        }
    };

    const getStatusColor = (status) => {
        const colors = {
            creating: 'status-creating',
            running: 'status-running',
            active: 'status-running',
            failed: 'status-failed',
            inactive: 'status-stopped'
        };
        return colors[status] || 'status-unknown';
    };

    return (
        <div className="services-page">
            <div className="page-header">
                <div>
                    <h1>Services</h1>
                    <p>Manage your deployed services</p>
                </div>
            </div>

            <div className="services-controls">
                <div className="search-box">
                    <Search size={18} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search services"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <button className="btn-secondary" onClick={loadServices}>
                    <Filter size={16} />
                    Refresh
                </button>
            </div>

            {loading ? (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading services...</p>
                </div>
            ) : filteredServices.length === 0 ? (
                <div className="empty-state">
                    <Package size={64} />
                    <h2>No services found</h2>
                    <p>
                        {searchQuery
                            ? 'No services match your search criteria'
                            : 'Create your first service to get started'}
                    </p>
                </div>
            ) : (
                <div className="services-grid">
                    {filteredServices.map((service) => (
                        <div
                            key={service.id}
                            className="service-card"
                            onClick={() => navigate(`/services/${service.id}`)}
                        >
                            <div className="service-header">
                                <h3>{service.name}</h3>
                                <span className={`status-badge ${getStatusColor(service.status)}`}>
                                    {service.status}
                                </span>
                            </div>
                            <div className="service-details">
                                <div className="detail-row">
                                    <span className="label">Template:</span>
                                    <span className="value">{service.template}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="label">Namespace:</span>
                                    <span className="value">{service.namespace}</span>
                                </div>
                                <div className="detail-row">
                                    <span className="label">Created:</span>
                                    <span className="value">
                                        {new Date(service.created_at).toLocaleString()}
                                    </span>
                                </div>
                            </div>
                            <div className="service-actions">
                                <button
                                    className="btn-text"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/services/${service.id}`);
                                    }}
                                >
                                    View Details
                                </button>
                                {JSON.parse(localStorage.getItem('user') || '{}').role === 'admin' && (
                                    <button
                                        className="btn-text danger"
                                        onClick={(e) => handleDelete(service.id, service.name, e)}
                                    >
                                        Delete
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Services;
