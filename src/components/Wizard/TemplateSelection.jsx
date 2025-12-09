import React from 'react';
import { templates } from '../../data/templates';
import { ArrowRight } from 'lucide-react';

const TemplateSelection = ({ onSelect }) => {
    return (
        <div className="animate-fade-in">
            <div className="mb-8">
                <h2 className="text-2xl font-bold mb-2">Choose a Template</h2>
                <p className="text-secondary">Select a template to bootstrap your new service.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
                {templates.map((template) => {
                    const Icon = template.icon;
                    return (
                        <button
                            key={template.id}
                            onClick={() => onSelect(template)}
                            className="card text-left group hover:border-accent transition-all duration-300 relative overflow-hidden"
                            style={{
                                backgroundColor: 'var(--bg-secondary)',
                                border: '1px solid var(--border-color)',
                                borderRadius: 'var(--radius-lg)',
                                padding: 'var(--spacing-lg)',
                                textAlign: 'left',
                                position: 'relative',
                                overflow: 'hidden',
                                display: 'flex',
                                flexDirection: 'column',
                                height: '100%'
                            }}
                        >
                            <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${template.bgColor} ${template.color}`}
                                style={{
                                    marginBottom: '1rem',
                                    width: '3rem',
                                    height: '3rem',
                                    borderRadius: '0.5rem',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    // Fallback styles if tailwind classes don't load immediately
                                }}
                            >
                                <Icon size={24} />
                            </div>

                            <h3 className="font-bold text-lg mb-2">{template.name}</h3>
                            <p className="text-sm text-secondary mb-4 line-clamp-2 flex-1" style={{ color: 'var(--text-secondary)', marginBottom: '1rem', flex: 1 }}>
                                {template.description}
                            </p>

                            <div className="flex flex-wrap gap-2 mt-auto">
                                {template.tags.map(tag => (
                                    <span
                                        key={tag}
                                        className="text-xs px-2 py-1 rounded-full bg-tertiary text-secondary"
                                        style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)', fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '9999px' }}
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>

                            {/* Hover Effect Overlay */}
                            <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default TemplateSelection;
