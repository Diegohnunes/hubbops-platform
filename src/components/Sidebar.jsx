import React from 'react';
import { LayoutDashboard, PlusCircle, Users, FileText, Settings, Box } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = () => {
    const location = useLocation();

    const menuItems = [
        { icon: PlusCircle, label: 'Create Service', path: '/create' },
        { icon: LayoutDashboard, label: 'Overview', path: '/' },
        { icon: Box, label: 'Services', path: '/services' },
        { icon: Users, label: 'Users & Groups', path: '/users' },
        { icon: FileText, label: 'Documentation', path: '/docs' },
    ];

    return (
        <aside className="w-64 h-screen bg-secondary border-r border-border fixed left-0 top-0 flex flex-col" style={{ backgroundColor: 'var(--bg-secondary)', borderRight: '1px solid var(--border-color)' }}>
            <div className="p-6 flex items-center gap-3 border-b border-border" style={{ borderBottom: '1px solid var(--border-color)' }}>
                <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center" style={{ backgroundColor: 'var(--accent-primary)' }}>
                    <span className="text-white font-bold">IDP</span>
                </div>
                <span className="font-bold text-lg">Portal</span>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;

                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${isActive
                                ? 'bg-accent/10 text-accent'
                                : 'text-secondary hover:bg-tertiary hover:text-primary'
                                }`}
                            style={{
                                backgroundColor: isActive ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                                color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                            }}
                        >
                            <Icon size={20} />
                            <span className="font-medium">{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-border" style={{ borderTop: '1px solid var(--border-color)' }}>
                <button className="flex items-center gap-3 px-4 py-3 w-full rounded-md text-secondary hover:bg-tertiary hover:text-primary transition-colors" style={{ color: 'var(--text-secondary)' }}>
                    <Settings size={20} />
                    <span className="font-medium">Settings</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
