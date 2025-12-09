import React from 'react';
import './Dashboards.css';

const Dashboards = () => {
    return (
        <div className="dashboards-page">
            <div className="page-header">
                <div>
                    <h1>Dashboards</h1>
                    <p>Monitor your services with detailed metrics and analytics</p>
                </div>
            </div>

            <div className="dashboards-grid">
                {/* Grafana Dashboard Embed Placeholder */}
                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <h3>Service Performance</h3>
                        <span className="dashboard-tag">Real-time</span>
                    </div>
                    <div className="dashboard-content">
                        <div className="dashboard-placeholder">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <line x1="12" y1="20" x2="12" y2="10"></line>
                                <line x1="18" y1="20" x2="18" y2="4"></line>
                                <line x1="6" y1="20" x2="6" y2="16"></line>
                            </svg>
                            <p>Performance metrics dashboard</p>
                            <span>Grafana integration coming soon</span>
                        </div>
                    </div>
                </div>

                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <h3>Resource Usage</h3>
                        <span className="dashboard-tag">Optimized</span>
                    </div>
                    <div className="dashboard-content">
                        <div className="dashboard-placeholder">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <circle cx="12" cy="12" r="10"></circle>
                                <path d="M12 6v6l4 2"></path>
                            </svg>
                            <p>CPU and memory usage</p>
                            <span>Real-time monitoring</span>
                        </div>
                    </div>
                </div>

                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <h3>Deployment Timeline</h3>
                        <span className="dashboard-tag">Historical</span>
                    </div>
                    <div className="dashboard-content">
                        <div className="dashboard-placeholder">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                            <p>Deployment history and trends</p>
                            <span>Track your releases</span>
                        </div>
                    </div>
                </div>

                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <h3>Error Tracking</h3>
                        <span className="dashboard-tag">Alerts</span>
                    </div>
                    <div className="dashboard-content">
                        <div className="dashboard-placeholder">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                            <p>Error rates and logs</p>
                            <span>Monitor service health</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="dashboard-info">
                <div className="info-card">
                    <div className="info-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="16" x2="12" y2="12"></line>
                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                    </div>
                    <div className="info-content">
                        <h4>Grafana Integration</h4>
                        <p>Dashboards will be automatically populated with Grafana panels for each deployed service. You can customize metrics and create custom dashboards through the Grafana UI.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboards;
