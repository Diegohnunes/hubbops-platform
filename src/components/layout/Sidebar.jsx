import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BarChart3, Plus, Boxes, Book, Settings, Layers, Users, Puzzle } from 'lucide-react';
import './Sidebar.css';

const Sidebar = () => {
    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Overview' },
        { path: '/dashboards', icon: BarChart3, label: 'Dashboards' },
        { path: '/create', icon: Plus, label: 'Create Service' },
        { path: '/services', icon: Boxes, label: 'Services' },
        { path: '/users', icon: Users, label: 'Users & Groups' },
        { path: '/plugins', icon: Puzzle, label: 'Plugins' },
        { path: '/docs', icon: Book, label: 'Documentation' },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <Layers className="sidebar-logo-icon" size={32} />
                    <span className="sidebar-logo-text">Hubbops</span>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((item) => {
                    // RBAC Logic
                    const user = JSON.parse(localStorage.getItem('user') || '{}');

                    // Hide Users & Groups and Plugins for Viewers
                    if ((item.path === '/users' || item.path === '/plugins') && user.role === 'viewer') {
                        return null;
                    }

                    // Note: Create Service is VISIBLE for Viewers, but they cannot select templates

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) =>
                                `sidebar-nav-item ${isActive ? 'active' : ''}`
                            }
                            end={item.path === '/'}
                        >
                            <item.icon size={20} />
                            <span>{item.label}</span>
                        </NavLink>
                    );
                })}
            </nav>

            <div className="sidebar-footer">
                {(() => {
                    try {
                        const user = JSON.parse(localStorage.getItem('user') || '{}');
                        if (user.role === 'admin') {
                            return (
                                <NavLink
                                    to="/settings"
                                    className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
                                >
                                    <Settings size={20} />
                                    <span>Settings</span>
                                </NavLink>
                            );
                        }
                    } catch (e) {
                        return null;
                    }
                    return null;
                })()}
            </div>
        </aside>
    );
};

export default Sidebar;
