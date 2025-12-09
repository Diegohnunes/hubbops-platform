import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ size = 'medium', message }) => {
    return (
        <div className="loading-container">
            <div className={`spinner ${size}`}>
                <div className="spinner-circle"></div>
            </div>
            {message && <p className="loading-message">{message}</p>}
        </div>
    );
};

export default LoadingSpinner;
