import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useTheme } from '../../utils/ThemeProvider';
import { SunIcon, MoonIcon, UserCircleIcon } from '@heroicons/react/24/solid';
import './Header.css';

const Header = () => {
    const { theme, toggleTheme } = useTheme();
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            navigate(`/services?search=${encodeURIComponent(searchQuery.trim())}`);
        }
    };

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
    };

    return (
        <header className="header">
            <form className="header-search" onSubmit={handleSearch}>
                <Search size={18} className="search-icon" />
                <input
                    type="text"
                    placeholder="         Search services"
                    value={searchQuery}
                    onChange={handleSearchChange}
                />
            </form>

            <div className="header-actions">
                <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
                    {theme === 'dark' ? (
                        <SunIcon className="w-6 h-6" />
                    ) : (
                        <MoonIcon className="w-6 h-6" />
                    )}
                </button>

                <button className="avatar-btn">
                    <UserCircleIcon className="w-6 h-6" />
                </button>
            </div>
        </header>
    );
};

export default Header;
