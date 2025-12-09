import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Puzzle, Plus, Search } from 'lucide-react';
import './Plugins.css';

const Plugins = () => {
    const navigate = useNavigate();

    useEffect(() => {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        if (currentUser.role === 'viewer') {
            navigate('/');
        }
    }, [navigate]);

    const mockPlugins = [
        { id: 1, name: 'Terraform Provider', description: 'Infrastructure as Code support', status: 'installed', version: '1.5.0' },
        { id: 2, name: 'GitHub Actions', description: 'CI/CD integration with GitHub', status: 'installed', version: '2.1.0' },
        { id: 3, name: 'Slack Notifications', description: 'Send alerts to Slack channels', status: 'available', version: '1.0.0' },
        { id: 4, name: 'DataDog Metrics', description: 'Export metrics to DataDog', status: 'available', version: '3.2.1' },
        { id: 5, name: 'PagerDuty Alerts', description: 'Incident management integration', status: 'available', version: '1.3.0' },
    ];

    return (
        <div className="plugins-page">
            <div className="page-header">
                <div>
                    <h1>Plugins</h1>
                    <p>Extend Hubbops with additional integrations</p>
                </div>
                <button className="btn-primary" disabled>
                    <Plus size={16} />
                    Install Plugin
                </button>
            </div>

            <div className="search-bar">
                <Search size={18} />
                <input type="text" placeholder="Search plugins..." />
            </div>

            <div className="plugins-grid">
                {mockPlugins.map(plugin => (
                    <div key={plugin.id} className="plugin-card">
                        <div className="plugin-icon">
                            <Puzzle size={32} />
                        </div>
                        <div className="plugin-info">
                            <h3>{plugin.name}</h3>
                            <p>{plugin.description}</p>
                            <div className="plugin-meta">
                                <span className="version">v{plugin.version}</span>
                                <span className={`status ${plugin.status}`}>
                                    {plugin.status === 'installed' ? '✓ Installed' : 'Available'}
                                </span>
                            </div>
                        </div>
                        <button
                            className={plugin.status === 'installed' ? 'btn-secondary' : 'btn-primary'}
                            disabled
                        >
                            {plugin.status === 'installed' ? 'Configure' : 'Install'}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Plugins;
