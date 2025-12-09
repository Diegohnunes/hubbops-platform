import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import FormField from './FormField';
import './DynamicForm.css';

const DynamicForm = ({ schema, onSubmit, onBack }) => {
    const [formData, setFormData] = useState({});
    const [errors, setErrors] = useState({});
    const [collapsedSections, setCollapsedSections] = useState({ 'Advanced Options': true });

    useEffect(() => {
        // Initialize default values
        if (schema && schema.fields) {
            const defaults = {};
            schema.fields.forEach(field => {
                if (field.default !== undefined && field.key) {
                    defaults[field.key] = field.default;
                }
            });
            setFormData(prev => ({ ...defaults, ...prev }));
        }
    }, [schema]);

    const handleChange = (key, value) => {
        setFormData(prev => ({ ...prev, [key]: value }));
        // Clear error when field changes
        if (errors[key]) {
            setErrors(prev => ({ ...prev, [key]: null }));
        }
    };

    const toggleSection = (sectionName) => {
        setCollapsedSections(prev => ({
            ...prev,
            [sectionName]: !prev[sectionName]
        }));
    };

    const validate = () => {
        const newErrors = {};
        let isValid = true;

        schema.fields.forEach(field => {
            if (field.required && field.key && !formData[field.key]) {
                newErrors[field.key] = 'This field is required';
                isValid = false;
            }
        });

        setErrors(newErrors);
        return isValid;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validate()) {
            onSubmit(formData);
        }
    };

    if (!schema) return <div>Loading form...</div>;

    // Group fields by sections
    const renderFields = () => {
        const elements = [];
        let currentSection = null;
        let sectionFields = [];

        const flushSection = () => {
            if (currentSection) {
                const isCollapsed = collapsedSections[currentSection];
                elements.push(
                    <div key={`section-${currentSection}`} className="form-section">
                        <button
                            type="button"
                            className="section-header"
                            onClick={() => toggleSection(currentSection)}
                        >
                            {isCollapsed ? <ChevronRight size={20} /> : <ChevronDown size={20} />}
                            <span>{currentSection}</span>
                        </button>
                        {!isCollapsed && (
                            <div className="section-fields">
                                {sectionFields}
                            </div>
                        )}
                    </div>
                );
                sectionFields = [];
            }
        };

        schema.fields.forEach((field, index) => {
            // Check if this is a section marker
            if (field.section) {
                flushSection();
                currentSection = field.section;
                return;
            }

            const fieldElement = (
                <FormField
                    key={field.key || `field-${index}`}
                    field={field}
                    value={formData[field.key]}
                    onChange={handleChange}
                    error={errors[field.key]}
                />
            );

            if (currentSection) {
                sectionFields.push(fieldElement);
            } else {
                elements.push(fieldElement);
            }
        });

        // Flush remaining section fields
        flushSection();

        return elements;
    };

    return (
        <form className="dynamic-form" onSubmit={handleSubmit}>
            <div className="form-fields">
                {renderFields()}
            </div>

            <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={onBack}>
                    Back
                </button>
                <button type="submit" className="btn-primary">
                    Next: Review
                </button>
            </div>
        </form>
    );
};

export default DynamicForm;
