import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function Login() {
    const navigate = useNavigate();
    const [isRegister, setIsRegister] = useState(false);
    const [form, setForm] = useState({
        email: '',
        password: '',
        name: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [firstTimeSetup, setFirstTimeSetup] = useState(null);

    // Check if this is first time setup
    React.useEffect(() => {
        fetch(`${API_BASE}/auth/status`)
            .then(res => res.json())
            .then(data => {
                setFirstTimeSetup(data.first_time_setup || false);
                if (data.first_time_setup) {
                    setIsRegister(true);
                }
                // If already authenticated, redirect
                if (data.authenticated) {
                    navigate('/');
                }
            })
            .catch(() => setFirstTimeSetup(false));
    }, [navigate]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const endpoint = isRegister ? '/auth/register' : '/auth/login';
            const body = isRegister
                ? { email: form.email, password: form.password, name: form.name }
                : { email: form.email, password: form.password };

            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            const data = await res.json();

            if (data.success && data.token) {
                // Store token
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));

                // Redirect to home
                navigate('/');
            } else {
                setError(data.message || 'Authentication failed');
            }
        } catch (err) {
            setError('Connection error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h1>HubbOps</h1>
                    <p>Internal Developer Platform</p>
                </div>

                {firstTimeSetup && (
                    <div className="first-time-notice">
                        <span className="icon">🎉</span>
                        <p>Welcome! Create your admin account to get started.</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="login-form">
                    {isRegister && (
                        <div className="form-group">
                            <label htmlFor="name">Name</label>
                            <input
                                type="text"
                                id="name"
                                value={form.name}
                                onChange={(e) => setForm({ ...form, name: e.target.value })}
                                placeholder="Your name"
                                required={isRegister}
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            value={form.email}
                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                            placeholder="you@example.com"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button
                        type="submit"
                        className="login-button"
                        disabled={loading}
                    >
                        {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
                    </button>
                </form>

                {/* Registration disabled for public users */}
                {/* Only available during first-time setup */}
            </div>
        </div>
    );
}

export default Login;
