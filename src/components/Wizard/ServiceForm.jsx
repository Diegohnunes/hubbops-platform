import React, { useState, useEffect } from 'react';

const ServiceForm = ({ template, onSubmit, onBack }) => {
    const [formData, setFormData] = useState({
        serviceName: '',
        description: '',
        owner: '',
        environment: [],
        tags: '',
    });

    // Initialize default values for template-specific fields
    useEffect(() => {
        if (template?.fields) {
            const defaults = {};
            template.fields.forEach(field => {
                if (field.default !== undefined) {
                    defaults[field.key] = field.default;
                }
            });
            setFormData(prev => ({ ...prev, ...defaults }));
        }
    }, [template]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;

        if (type === 'checkbox') {
            if (name === 'environment') {
                // Handle multi-select checkbox for environment
                const updatedEnv = checked
                    ? [...(formData.environment || []), value]
                    : (formData.environment || []).filter(env => env !== value);
                setFormData(prev => ({ ...prev, [name]: updatedEnv }));
            } else {
                // Normal boolean checkbox
                setFormData(prev => ({ ...prev, [name]: checked }));
            }
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="animate-fade-in max-w-4xl">
            <div className="flex gap-8">
                {/* Left Column: Common Fields */}
                <div className="flex-1 space-y-6">
                    <div className="card" style={{ backgroundColor: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
                        <h3 className="text-lg font-bold mb-4 border-b border-border pb-2" style={{ borderBottom: '1px solid var(--border-color)' }}>General Information</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1 text-secondary" style={{ color: 'var(--text-secondary)' }}>Service Name</label>
                                <input
                                    type="text"
                                    name="serviceName"
                                    value={formData.serviceName}
                                    onChange={handleChange}
                                    className="w-full bg-primary border border-border rounded-md px-3 py-2 text-primary focus:border-accent outline-none transition-colors"
                                    style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                    placeholder="e.g., my-new-service"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-secondary" style={{ color: 'var(--text-secondary)' }}>Description</label>
                                <textarea
                                    name="description"
                                    value={formData.description}
                                    onChange={handleChange}
                                    className="w-full bg-primary border border-border rounded-md px-3 py-2 text-primary focus:border-accent outline-none transition-colors h-24 resize-none"
                                    style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                    placeholder="What does this service do?"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-secondary" style={{ color: 'var(--text-secondary)' }}>Owner</label>
                                <select
                                    name="owner"
                                    value={formData.owner}
                                    onChange={handleChange}
                                    className="w-full bg-primary border border-border rounded-md px-3 py-2 text-primary focus:border-accent outline-none transition-colors"
                                    style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                    required
                                >
                                    <option value="">Select Owner...</option>
                                    <option value="team-platform">Platform Team</option>
                                    <option value="team-backend">Backend Team</option>
                                    <option value="team-frontend">Frontend Team</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2 text-secondary" style={{ color: 'var(--text-secondary)' }}>Environments</label>
                                <div className="flex gap-4">
                                    {['dev', 'stg', 'prod'].map(env => (
                                        <label key={env} className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="checkbox"
                                                name="environment"
                                                value={env}
                                                checked={(formData.environment || []).includes(env)}
                                                onChange={handleChange}
                                                className="accent-accent"
                                                style={{ accentColor: 'var(--accent-primary)' }}
                                            />
                                            <span className="text-sm uppercase font-medium">{env}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Template Specifics */}
                <div className="flex-1 space-y-6">
                    <div className="card" style={{ backgroundColor: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
                        <h3 className="text-lg font-bold mb-4 border-b border-border pb-2" style={{ borderBottom: '1px solid var(--border-color)' }}>
                            {template.name} Configuration
                        </h3>

                        <div className="space-y-4">
                            {template.fields && template.fields.map(field => (
                                <div key={field.key}>
                                    <label className="block text-sm font-medium mb-1 text-secondary" style={{ color: 'var(--text-secondary)' }}>
                                        {field.label}
                                    </label>

                                    {field.type === 'select' ? (
                                        <select
                                            name={field.key}
                                            value={formData[field.key] || ''}
                                            onChange={handleChange}
                                            className="w-full bg-primary border border-border rounded-md px-3 py-2 text-primary focus:border-accent outline-none transition-colors"
                                            style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                        >
                                            {field.options.map(opt => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                    ) : field.type === 'boolean' ? (
                                        <label className="flex items-center gap-2 cursor-pointer mt-2">
                                            <input
                                                type="checkbox"
                                                name={field.key}
                                                checked={!!formData[field.key]}
                                                onChange={handleChange}
                                                className="accent-accent"
                                                style={{ accentColor: 'var(--accent-primary)' }}
                                            />
                                            <span className="text-sm text-secondary" style={{ color: 'var(--text-secondary)' }}>Enable {field.label}</span>
                                        </label>
                                    ) : (
                                        <input
                                            type={field.type || 'text'}
                                            name={field.key}
                                            value={formData[field.key] || ''}
                                            onChange={handleChange}
                                            className="w-full bg-primary border border-border rounded-md px-3 py-2 text-primary focus:border-accent outline-none transition-colors"
                                            style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                            placeholder={field.placeholder || ''}
                                        />
                                    )}
                                </div>
                            ))}

                            {!template.fields && (
                                <p className="text-muted italic">No specific configuration for this template.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button
                    type="button"
                    onClick={onBack}
                    className="btn text-secondary hover:text-primary"
                    style={{ color: 'var(--text-secondary)' }}
                >
                    Back
                </button>
                <button
                    type="submit"
                    className="btn btn-primary px-8"
                    style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}
                >
                    Review & Create
                </button>
            </div>
        </form>
    );
};

export default ServiceForm;
