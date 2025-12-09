import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, Loader, ChevronDown, ChevronRight } from 'lucide-react';
import './LogViewer.css';

const LogViewer = ({ serviceId, onComplete }) => {
    const [logMessages, setLogMessages] = useState([]);
    const [steps, setSteps] = useState([]);
    const [expandedSteps, setExpandedSteps] = useState(new Set());
    const [isComplete, setIsComplete] = useState(false);
    const [hasFailed, setHasFailed] = useState(false);
    const logsEndRef = useRef(null);
    const wsRef = useRef(null);

    useEffect(() => {
        const ws = new WebSocket(`ws://localhost:8000/api/services/ws/${serviceId}/logs`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            const logMessage = JSON.parse(event.data);
            setLogMessages(prev => [...prev, logMessage]);

            if (logMessage.step) {
                setSteps(prev => {
                    const existing = prev.find(s => s.name === logMessage.step);
                    if (existing) {
                        return prev.map(s =>
                            s.name === logMessage.step
                                ? { ...s, status: logMessage.level === 'error' ? 'failed' : 'running', messages: [...s.messages, logMessage] }
                                : s
                        );
                    } else {
                        return [...prev, {
                            name: logMessage.step,
                            status: 'running',
                            messages: [logMessage]
                        }];
                    }
                });

                setExpandedSteps(prev => new Set([...prev, logMessage.step]));
            }

            if (logMessage.level === 'error') setHasFailed(true);
            if (logMessage.message.includes('successfully')) setIsComplete(true);
        };

        ws.onclose = () => {
            setIsComplete(true);
            if (onComplete) onComplete();
        };

        ws.onerror = () => setHasFailed(true);

        return () => wsRef.current?.close();
    }, [serviceId, onComplete]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logMessages]);

    const toggleStep = (stepName) => {
        setExpandedSteps(prev => {
            const newSet = new Set(prev);
            if (newSet.has(stepName)) {
                newSet.delete(stepName);
            } else {
                newSet.add(stepName);
            }
            return newSet;
        });
    };

    const getStepIcon = (status) => {
        if (status === 'running') return <Loader size={16} className="spin" />;
        if (status === 'failed') return <XCircle size={16} className="error-icon" />;
        return <CheckCircle size={16} className="success-icon" />;
    };

    const getLevelClass = (level) => {
        const classes = {
            info: 'log-info',
            warning: 'log-warning',
            error: 'log-error',
            success: 'log-success'
        };
        return classes[level] || 'log-info';
    };

    return (
        <div className="log-viewer">
            <div className="log-header">
                <h3>Service Creation Logs</h3>
                {isComplete && !hasFailed && <span className="status-badge success">✓ Completed</span>}
                {hasFailed && <span className="status-badge error">✗ Failed</span>}
                {!isComplete && !hasFailed && (
                    <span className="status-badge running">
                        <Loader size={14} className="spin" /> Running...
                    </span>
                )}
            </div>

            <div className="log-content">
                {steps.length > 0 ? (
                    <div className="steps-list">
                        {steps.map((step) => (
                            <div key={step.name} className={`step-item ${step.status}`}>
                                <div className="step-header" onClick={() => toggleStep(step.name)}>
                                    <div className="step-info">
                                        {getStepIcon(step.status)}
                                        <span className="step-name">{step.name}</span>
                                        <span className="step-count">{step.messages.length} messages</span>
                                    </div>
                                    {expandedSteps.has(step.name) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                </div>

                                {expandedSteps.has(step.name) && (
                                    <div className="step-messages">
                                        {step.messages.map((msg, idx) => (
                                            <div key={idx} className={`log-line ${getLevelClass(msg.level)}`}>
                                                <span className="log-timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                                                <span className="log-message">{msg.message}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="all-messages">
                        {logMessages.map((msg, idx) => (
                            <div key={idx} className={`log-line ${getLevelClass(msg.level)}`}>
                                <span className="log-timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                                <span className="log-message">{msg.message}</span>
                            </div>
                        ))}
                    </div>
                )}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
};

export default LogViewer;
