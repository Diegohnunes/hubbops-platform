import React, { useState, useEffect } from 'react';
import { Search, Sun, Moon, Bell } from 'lucide-react';
import './Topbar.css';

const Topbar = () => {
    const [theme, setTheme] = useState('dark');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    return (
        <header className="topbar">

            {/* Search */}
            <div className="search-container improved">
                <Search className="search-icon improved" size={18} />
                <input
                    type="text"
                    placeholder="Search services"
                    className="search-input improved"
                />
            </div>

            {/* Actions */}
            <div className="topbar-actions">

                {/* Theme toggle */}
                <button
                    onClick={toggleTheme}
                    className="icon-button improved"
                    aria-label="Toggle theme"
                >
                    {theme === 'dark'
                        ? <Sun size={18} strokeWidth={1.7} />
                        : <Moon size={18} strokeWidth={1.7} />
                    }
                </button>

                {/* Notifications */}
                <button
                    className="icon-button improved notification-button"
                    aria-label="Notifications"
                >
                    <Bell size={18} strokeWidth={1.7} />
                    <span className="notification-dot"></span>
                </button>

                {/* Profile */}
                <button className="profile-button improved" aria-label="User profile">
                    <div className="avatar">
                        D
                    </div>
                </button>

            </div>
        </header>
    );
};

export default Topbar;
