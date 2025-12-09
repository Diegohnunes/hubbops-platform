import React, { useState } from 'react';
import { Info } from 'lucide-react';
import './FormField.css';

const FormField = ({ field, value, onChange, error }) => {
    const [isCustom, setIsCustom] = useState(false);
    const [customValue, setCustomValue] = useState('');

    const handleChange = (e) => {
        const val = field.type === 'boolean' ? e.target.checked : e.target.value;

        // Handle select-or-custom type
        if (field.type === 'select-or-custom') {
            if (val === 'custom') {
                setIsCustom(true);
                onChange(field.key, customValue || '');
            } else {
                setIsCustom(false);
                onChange(field.key, val);
            }
        } else {
            onChange(field.key, val);
        }
    };

    const handleCustomChange = (e) => {
        const val = e.target.value;
        setCustomValue(val);
        onChange(field.key, val);
    };

    return (
        <div className={`form-field ${field.type}`}>
            <div className="field-label-container">
                <label htmlFor={field.key} className="field-label">
                    {field.label}
                    {field.required && <span className="required-mark">*</span>}
                </label>
                {field.description && (
                    <div className="field-tooltip" title={field.description}>
                        <Info size={14} />
                    </div>
                )}
            </div>

            <div className="field-input-container">
                {field.type === 'text' && (
                    <input
                        type="text"
                        id={field.key}
                        value={value || ''}
                        onChange={handleChange}
                        placeholder={field.placeholder}
                        className={`input-text ${error ? 'error' : ''}`}
                    />
                )}

                {field.type === 'number' && (
                    <input
                        type="number"
                        id={field.key}
                        value={value || ''}
                        onChange={handleChange}
                        min={field.min}
                        max={field.max}
                        className={`input-number ${error ? 'error' : ''}`}
                    />
                )}

                {field.type === 'select' && (
                    <select
                        id={field.key}
                        value={value || field.default || ''}
                        onChange={handleChange}
                        className={`input-select ${error ? 'error' : ''}`}
                    >
                        {field.options.map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                        ))}
                    </select>
                )}

                {field.type === 'select-or-custom' && (
                    <>
                        <select
                            id={field.key}
                            value={isCustom ? 'custom' : value || field.default || ''}
                            onChange={handleChange}
                            className={`input-select ${error ? 'error' : ''}`}
                        >
                            {field.options.map(opt => (
                                <option key={opt} value={opt}>
                                    {opt === 'custom' ? '🔧 Custom...' : opt}
                                </option>
                            ))}
                        </select>
                        {isCustom && (
                            <input
                                type="text"
                                value={customValue}
                                onChange={handleCustomChange}
                                placeholder={field.customPlaceholder || 'Enter custom value'}
                                className={`input-text custom-input ${error ? 'error' : ''}`}
                            />
                        )}
                    </>
                )}

                {field.type === 'boolean' && (
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            id={field.key}
                            checked={value || false}
                            onChange={handleChange}
                        />
                        <span className="slider round"></span>
                    </label>
                )}
            </div>

            {error && <span className="field-error">{error}</span>}
            {field.description && <p className="field-help-text">{field.description}</p>}
        </div>
    );
};

export default FormField;
