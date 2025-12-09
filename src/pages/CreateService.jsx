import React, { useState, useEffect } from 'react';
import TemplateGrid from '../components/templates/TemplateGrid';
import DynamicForm from '../components/forms/DynamicForm';
import ReviewStep from '../components/wizard/ReviewStep';
import LoadingSpinner from '../components/common/LoadingSpinner';
import LogViewer from '../components/viewer/LogViewer';
import { apiClient } from '../utils/api';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import './CreateService.css';

const CreateService = () => {
    const [step, setStep] = useState(1);
    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [schema, setSchema] = useState(null);
    const [formData, setFormData] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [createdServiceId, setCreatedServiceId] = useState(null);

    // RBAC: Viewer verification is handled at the template level (cannot select)

    const handleTemplateSelect = async (template) => {
        setSelectedTemplate(template);
        setError(null);

        // Fetch schema for the selected template
        if (template.schema) {
            setLoading(true);
            try {
                const response = await fetch(template.schema);
                if (!response.ok) throw new Error('Failed to load template schema');
                const data = await response.json();
                setSchema(data);
                setStep(2);
            } catch (err) {
                console.error('Error loading schema:', err);
                setError(`Failed to load template: ${err.message}`);
            } finally {
                setLoading(false);
            }
        } else {
            setStep(2);
        }
    };

    const handleFormSubmit = (data) => {
        setFormData(data);
        setStep(3);
    };

    const handleCreateService = async () => {
        try {
            const payload = {
                template_id: selectedTemplate.id,
                service_name: formData.service_name,
                config: formData
            };

            const response = await apiClient.createService(payload);

            if (response.success) {
                setCreatedServiceId(response.service_id);
                setStep(4); // Go to logs view
            }
        } catch (error) {
            console.error('Failed to create service:', error);
            setError(`Failed to create service: ${error.message}`);
        }
    };

    return (
        <div className="create-service-page">
            <div className="wizard-header">
                <div className="wizard-steps">
                    <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                        <div className="step-number">1</div>
                        <span className="step-label">Select Template</span>
                    </div>
                    <div className="step-separator" />
                    <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
                        <div className="step-number">2</div>
                        <span className="step-label">Configure</span>
                    </div>
                    <div className="step-separator" />
                    <div className={`step ${step >= 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}>
                        <div className="step-number">3</div>
                        <span className="step-label">Review</span>
                    </div>
                    <div className="step-separator" />
                    <div className={`step ${step >= 4 ? 'active' : ''}`}>
                        <div className="step-number">4</div>
                        <span className="step-label">Deploy</span>
                    </div>
                </div>
            </div>

            <div className="wizard-content">
                {loading && (
                    <LoadingSpinner message="Loading template schema..." />
                )}

                {error && (
                    <div className="error-message">
                        <p>{error}</p>
                        <button className="btn-secondary" onClick={() => { setError(null); setStep(1); }}>
                            Try Again
                        </button>
                    </div>
                )}

                {!loading && !error && step === 1 && (
                    <div className="step-content fade-in">
                        <div className="step-header">
                            <h2>Create a New Service</h2>
                            <p>Choose a template to begin creating your service</p>
                        </div>
                        <TemplateGrid onSelectTemplate={handleTemplateSelect} />
                    </div>
                )}

                {step === 2 && (
                    <div className="step-content fade-in">
                        <div className="step-header-row">
                            <div className="step-header">
                                <h2>Configure {selectedTemplate?.name}</h2>
                                <p>Fill in the details for your new service</p>
                            </div>
                        </div>

                        <DynamicForm
                            schema={schema}
                            onSubmit={handleFormSubmit}
                            onBack={() => setStep(1)}
                        />
                    </div>
                )}

                {step === 3 && (
                    <div className="step-content fade-in">
                        <div className="step-header">
                            <h2>Review & Create</h2>
                            <p>Verify your configuration before deployment</p>
                        </div>

                        <ReviewStep
                            template={selectedTemplate}
                            formData={formData}
                            onBack={() => setStep(2)}
                            onCreate={handleCreateService}
                        />
                    </div>
                )}

                {step === 4 && (
                    <div className="step-content fade-in">
                        <div className="step-header">
                            <h2>Deploying {selectedTemplate?.name}</h2>
                            <p>Watch the deployment progress in real-time</p>
                        </div>

                        <LogViewer
                            serviceId={createdServiceId}
                            onComplete={() => {
                                // Navigate to services page after completion
                                setTimeout(() => {
                                    window.location.href = '/services';
                                }, 2000);
                            }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

export default CreateService;
