import React from 'react';
import { NavLink } from 'react-router-dom';
import { Box, Code, Layout, Database, Layers, Cloud, Zap, FileJson, TrendingUp, HelpCircle } from 'lucide-react';
import './TemplateCard.css';

const iconMap = {
    'box': Box,
    'python': Code,
    'code': Code,
    'layout': Layout,
    'database': Database,
    'layers': Layers,
    'cloud': Cloud,
    'zap': Zap,
    'file-json': FileJson,
    'trending-up': TrendingUp
};

const TemplateCard = ({ template, onSelect }) => {
    const IconComponent = iconMap[template.icon] || HelpCircle;
    const isReady = template.status === 'ready';
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const canSelect = user.role !== 'viewer';

    return (
        <div className={`template-card ${template.status}`}>
            <div className={`template-icon-wrapper ${template.status}`}>
                <IconComponent size={32} />
            </div>

            <div className="template-content">
                <div className="template-header">
                    <h3>{template.name}</h3>
                    <span className={`badge ${template.status}`}>
                        {isReady ? 'Ready' : 'Coming Soon'}
                    </span>
                </div>

                <p className="template-description">{template.description}</p>

                <div className="template-tags">
                    {template.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                    ))}
                </div>
            </div>

            {isReady && canSelect && (
                <div className="template-action">
                    <button
                        className="btn-select"
                        onClick={() => onSelect(template)}
                    >
                        Select Template
                    </button>
                </div>
            )}
        </div>
    );
};

export default TemplateCard;
