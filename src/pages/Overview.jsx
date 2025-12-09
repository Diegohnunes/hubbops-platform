import React, { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import './Overview.css';

const Overview = () => {
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [templates, setTemplates] = useState([]);
    const [stats, setStats] = useState({
        total: 0,
        running: 0,
        creating: 0,
        failed: 0,
        inactive: 0
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            // Fetch all services including deleted ones for activity history
            const [servicesData, templatesData] = await Promise.all([
                apiClient.listServices(true),
                apiClient.getTemplates()
            ]);

            const allServices = servicesData.services || [];
            setServices(allServices);
            setTemplates(templatesData || []);

            // Filter active services for stats
            const activeServices = allServices.filter(s => s.status !== 'deleted');

            // Calculate stats based on active services only
            const stats = {
                total: activeServices.length,
                running: activeServices.filter(s => s.status === 'active' || s.status === 'running').length,
                creating: activeServices.filter(s => s.status === 'creating').length,
                failed: activeServices.filter(s => s.status === 'failed').length,
                inactive: activeServices.filter(s => s.status === 'inactive').length
            };
            setStats(stats);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getRecentActivity = () => {
        return services
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 5);
    };

    const getStatusColor = (status) => {
        const colors = {
            creating: 'warning',
            active: 'success',
            running: 'success',
            failed: 'error',
            inactive: 'neutral',
            deleted: 'error'
        };
        return colors[status] || 'neutral';
    };

    const formatTimeAgo = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    };

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <div>
                    <h1>Overview</h1>
                    <p className="dashboard-subtitle">
                        Welcome to Hubbops - Your Internal Developer Platform
                    </p>
                </div>
            </div>

            {loading ? (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading overview...</p>
                </div>
            ) : (
                <>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-label">Total Services</div>
                            <div className="stat-value">{stats.total}</div>
                            <div className="stat-trend neutral">
                                {stats.inactive > 0 ? `${stats.inactive} inactive` : 'All active'}
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Running</div>
                            <div className="stat-value success">{stats.running}</div>
                            <div className={`stat-trend ${stats.running > 0 ? 'positive' : 'neutral'}`}>
                                {stats.running > 0 ? `${stats.running} active` : '—'}
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Templates</div>
                            <div className="stat-value primary">{templates.length}</div>
                            <div className="stat-trend neutral">
                                {templates.filter(t => t.status === 'coming-soon').length} Coming Soon
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Failed</div>
                            <div className="stat-value warning">{stats.failed}</div>
                            <div className={`stat-trend ${stats.failed > 0 ? 'negative' : 'positive'}`}>
                                {stats.failed > 0 ? `${stats.failed} failed` : 'All healthy'}
                            </div>
                        </div>
                    </div>

                    <div className="dashboard-section">
                        <h2>Quick Actions</h2>
                        <div className="quick-actions">
                            <a href="/create" className="action-card">
                                <div className="action-icon primary">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <line x1="12" y1="5" x2="12" y2="19"></line>
                                        <line x1="5" y1="12" x2="19" y2="12"></line>
                                    </svg>
                                </div>
                                <div className="action-content">
                                    <h3>Create Service</h3>
                                    <p>Deploy a new service using our templates</p>
                                </div>
                            </a>

                            <a href="/services" className="action-card">
                                <div className="action-icon success">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <rect x="3" y="3" width="7" height="7"></rect>
                                        <rect x="14" y="3" width="7" height="7"></rect>
                                        <rect x="14" y="14" width="7" height="7"></rect>
                                        <rect x="3" y="14" width="7" height="7"></rect>
                                    </svg>
                                </div>
                                <div className="action-content">
                                    <h3>View Services</h3>
                                    <p>Manage your running services</p>
                                </div>
                            </a>

                            <a href="/docs" className="action-card">
                                <div className="action-icon info">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                                    </svg>
                                </div>
                                <div className="action-content">
                                    <h3>Documentation</h3>
                                    <p>Learn how to use Hubbops</p>
                                </div>
                            </a>
                        </div>
                    </div>

                    <div className="dashboard-section">
                        <h2>Recent Activity</h2>
                        <div className="activity-card">
                            {getRecentActivity().length === 0 ? (
                                <div className="empty-state">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <line x1="12" y1="8" x2="12" y2="12"></line>
                                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                    </svg>
                                    <p>No recent activity</p>
                                    <span>Create your first service to get started</span>
                                </div>
                            ) : (
                                <div className="activity-list">
                                    {getRecentActivity().map((service) => (
                                        <div key={service.id} className="activity-item">
                                            <div className="activity-icon">
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                    <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                                                    <line x1="9" y1="9" x2="15" y2="9"></line>
                                                    <line x1="9" y1="15" x2="15" y2="15"></line>
                                                </svg>
                                            </div>
                                            <div className="activity-details">
                                                <div className="activity-title">
                                                    Service <strong>{service.name}</strong> {service.status === 'deleted' ? 'deleted' : 'created'}
                                                </div>
                                                <div className="activity-meta">
                                                    Template: {service.template} • {formatTimeAgo(service.created_at)}
                                                </div>
                                            </div>
                                            <span className={`status-badge status-${getStatusColor(service.status)}`}>
                                                {service.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default Overview;
