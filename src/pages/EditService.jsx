import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, AlertCircle } from 'lucide-react';
import { apiClient } from '../utils/api';
import DynamicForm from '../components/forms/DynamicForm';
import './CreateService.css';
import './EditService.css';

const EditService = () => {
    const { serviceId } = useParams();
    const navigate = useNavigate();
    const [service, setService] = useState(null);
    const [schema, setSchema] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadServiceAndSchema();
    }, [serviceId]);

    const loadServiceAndSchema = async () => {
        try {
            setLoading(true);
            setError(null);

            // Load service data
            const serviceData = await apiClient.getService(serviceId);
            setService(serviceData);

            // Load schema for the template
            if (serviceData.template) {
                try {
                    const schemaResponse = await fetch(`/templates/${serviceData.template}.json`);
                    if (schemaResponse.ok) {
                        const schemaData = await schemaResponse.json();
                        // Pre-fill form with existing config
                        schemaData.initialValues = serviceData.config || {};
                        setSchema(schemaData);
                    }
                } catch (schemaErr) {
                    console.warn('Could not load template schema:', schemaErr);
                }
            }
        } catch (err) {
            setError(err.message || 'Failed to load service');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (formData) => {
        // For now, just show the data that would be saved
        alert('Edit functionality coming soon!\n\nData that would be saved:\n' + JSON.stringify(formData, null, 2));
        // In the future: await apiClient.updateService(serviceId, formData);
    };

    const handleBack = () => {
        navigate(`/services/${serviceId}`);
    };

    if (loading) {
        return (
            <div className="create-service-page">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading service...</p>
                </div>
            </div>
        );
    }

    if (error || !service) {
        return (
            <div className="create-service-page">
                <div className="error-state">
                    <AlertCircle size={64} />
                    <h2>Error Loading Service</h2>
                    <p>{error || 'Service not found'}</p>
                    <button className="btn-primary" onClick={() => navigate('/services')}>
                        Back to Services
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="create-service-page">
            <div className="page-header">
                <button className="btn-back" onClick={handleBack}>
                    <ArrowLeft size={20} />
                    Back to Service
                </button>
                <div>
                    <h1>Edit Service: {service.name}</h1>
                    <p>Modify the configuration for this service</p>
                </div>
            </div>

            <div className="service-info-card">
                <h3>Current Service Details</h3>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="label">Service ID</span>
                        <span className="value">{service.id}</span>
                    </div>
                    <div className="info-item">
                        <span className="label">Template</span>
                        <span className="value">{service.template}</span>
                    </div>
                    <div className="info-item">
                        <span className="label">Namespace</span>
                        <span className="value">{service.namespace}</span>
                    </div>
                    <div className="info-item">
                        <span className="label">Status</span>
                        <span className="value">{service.status}</span>
                    </div>
                </div>
            </div>

            {schema ? (
                <DynamicForm
                    schema={{
                        ...schema,
                        fields: schema.fields.map(field => ({
                            ...field,
                            default: service.config?.[field.key] ?? field.default
                        }))
                    }}
                    onSubmit={handleSubmit}
                    onBack={handleBack}
                />
            ) : (
                <div className="no-schema">
                    <h3>Configuration</h3>
                    <pre>{JSON.stringify(service.config || {}, null, 2)}</pre>
                    <div className="form-actions">
                        <button className="btn-secondary" onClick={handleBack}>
                            Back
                        </button>
                        <button className="btn-primary" disabled>
                            <Save size={16} />
                            Save Changes (Coming Soon)
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EditService;
