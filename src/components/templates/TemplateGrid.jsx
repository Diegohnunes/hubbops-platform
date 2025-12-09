import React, { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';
import TemplateCard from './TemplateCard';
import './TemplateGrid.css';

const TemplateGrid = ({ onSelectTemplate }) => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('All');
    const [search, setSearch] = useState('');

    useEffect(() => {
        // Fetch templates from backend API
        fetch('/api/templates/')
            .then(res => res.json())
            .then(data => {
                // API returns array directly, not wrapped in {templates: [...]}
                setTemplates(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error loading templates:', err);
                setLoading(false);
            });
    }, []);

    const categories = ['All', ...new Set(templates.map(t => t.category))];

    // Sort categories: All first, then alphabetically, Others last
    const sortedCategories = categories.filter(c => c !== 'All' && c !== 'Others').sort();
    const finalCategories = ['All', ...sortedCategories];
    if (categories.includes('Others')) {
        finalCategories.push('Others');
    }

    const filteredTemplates = templates.filter(template => {
        const matchesCategory = filter === 'All' || template.category === filter;
        const matchesSearch = template.name.toLowerCase().includes(search.toLowerCase()) ||
            template.description.toLowerCase().includes(search.toLowerCase()) ||
            template.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()));
        return matchesCategory && matchesSearch;
    });

    if (loading) {
        return <div className="loading-grid">Loading templates...</div>;
    }

    return (
        <div className="template-grid-container">
            <div className="template-controls">
                <div className="category-filters">
                    {finalCategories.map(category => (
                        <button
                            key={category}
                            className={`filter-btn ${filter === category ? 'active' : ''}`}
                            onClick={() => setFilter(category)}
                        >
                            {category}
                        </button>
                    ))}
                </div>

                <div className="template-search">
                    <Search size={16} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search templates..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="templates-grid">
                {filteredTemplates.map(template => (
                    <TemplateCard
                        key={template.id}
                        template={template}
                        onSelect={onSelectTemplate}
                    />
                ))}
            </div>

            {filteredTemplates.length === 0 && (
                <div className="no-results">
                    <p>No templates found matching your criteria.</p>
                    <button className="btn-clear" onClick={() => { setFilter('All'); setSearch(''); }}>
                        Clear Filters
                    </button>
                </div>
            )}
        </div>
    );
};

export default TemplateGrid;
