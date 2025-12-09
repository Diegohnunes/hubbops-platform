import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Shield, Plus, Search, MoreVertical, Loader } from 'lucide-react';
import './UsersGroups.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const UsersGroups = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('users');
    const [searchQuery, setSearchQuery] = useState('');
    const [users, setUsers] = useState([]);
    const [groups, setGroups] = useState([]); // Real groups state
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);

    // Permission definitions
    const AVAILABLE_PERMISSIONS = [
        { id: 'services:read', label: 'View Services' },
        { id: 'services:create', label: 'Create Services' },
        { id: 'services:update', label: 'Edit Services' },
        { id: 'services:delete', label: 'Delete Services' },
        { id: 'users:read', label: 'View Users' },
        { id: 'users:create', label: 'Create Users' },
        { id: 'users:update', label: 'Edit Users' },
        { id: 'users:delete', label: 'Delete Users' },
        { id: 'group:read', label: 'View Groups' },
        { id: 'group:manage', label: 'Manage Groups' },
        { id: 'admin:all', label: 'Full Admin Access' },
    ];

    useEffect(() => {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        if (currentUser.role === 'viewer') {
            navigate('/');
            return;
        }
        setIsAdmin(currentUser.role === 'admin');
        fetchUsers();
        fetchGroups();
    }, [navigate]);

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem('token');
            const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

            if (currentUser?.role !== 'admin') {
                setUsers([currentUser]);
                return;
            }

            const res = await fetch(`${API_BASE}/auth/users`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Failed to fetch users');
            const data = await res.json();
            setUsers(data);
        } catch (err) {
            console.error(err);
            setError('Failed to load users');
        }
    };

    const fetchGroups = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            // Allow all authenticated users to see groups for now, or restrict based on role?
            // Endpoints are require_admin protected currently.
            // If user is not admin, we may assume they can't CRUD groups, but can they view?
            // The API list_groups is protected require_admin.
            const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
            if (currentUser.role !== 'admin') {
                setGroups([]); // Or mock for dev/viewer if needed, but best to stick to RBAC
                return;
            }

            const res = await fetch(`${API_BASE}/groups/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Failed to fetch groups');
            const data = await res.json();
            setGroups(data);
        } catch (err) {
            console.error(err);
            // Don't set main error if just groups fail, maybe?
            // setError('Failed to load groups');
        } finally {
            setLoading(false);
        }
    };

    // ... (Helper functions like getRoleBadgeClass remain same)
    const getRoleBadgeClass = (role) => {
        const classes = { 'admin': 'badge-admin', 'developer': 'badge-developer', 'viewer': 'badge-viewer' };
        return classes[role?.toLowerCase()] || 'badge-default';
    };

    const filteredUsers = users.filter(user =>
        user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredGroups = groups.filter(group =>
        group.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalType, setModalType] = useState('user'); // 'user' or 'group'
    const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
    const [selectedItem, setSelectedItem] = useState(null); // User or Group object

    // Form Data
    const [userFormData, setUserFormData] = useState({ name: '', email: '', password: '', role: 'viewer' });
    const [groupFormData, setGroupFormData] = useState({ name: '', description: '', permissions: [] });

    // Handlers
    const handleOpenAddUser = () => {
        setModalType('user');
        setModalMode('add');
        setUserFormData({ name: '', email: '', password: '', role: 'viewer', group_ids: [] });
        setIsModalOpen(true);
    };

    const handleOpenAddGroup = () => {
        setModalType('group');
        setModalMode('add');
        setGroupFormData({ name: '', description: '', permissions: [] });
        setIsModalOpen(true);
    };

    const handleEditUser = (user) => {
        setModalType('user');
        setModalMode('edit');
        setSelectedItem(user);
        // Ensure group_ids are loaded if available in user object
        setUserFormData({
            name: user.name,
            role: user.role,
            group_ids: user.group_ids || []
        });
        setIsModalOpen(true);
    };

    const handleEditGroup = (group) => {
        setModalType('group');
        setModalMode('edit');
        setSelectedItem(group);
        setGroupFormData({
            name: group.name,
            description: group.description,
            permissions: group.permissions || []
        });
        setIsModalOpen(true);
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm('Are you sure you want to delete this user?')) return;
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/auth/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to delete user');
            fetchUsers();
        } catch (err) {
            alert(err.message);
        }
    };

    const handleDeleteGroup = async (groupId) => {
        if (!window.confirm('Are you sure you want to delete this group?')) return;
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/groups/${groupId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to delete group');
            fetchGroups();
        } catch (err) {
            alert(err.message);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            let url, method, body;

            if (modalType === 'user') {
                url = modalMode === 'add' ? `${API_BASE}/auth/register` : `${API_BASE}/auth/users/${selectedItem.id}`;
                method = modalMode === 'add' ? 'POST' : 'PATCH';
                body = { ...userFormData };
                if (modalMode === 'edit') { delete body.password; delete body.email; }
            } else {
                url = modalMode === 'add' ? `${API_BASE}/groups/` : `${API_BASE}/groups/${selectedItem.id}`;
                method = modalMode === 'add' ? 'POST' : 'PATCH';
                body = { ...groupFormData };
            }

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(body)
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.message || data.detail || 'Operation failed');
            }

            modalType === 'user' ? fetchUsers() : fetchGroups();
            setIsModalOpen(false);
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const togglePermission = (permId) => {
        setGroupFormData(prev => {
            const perms = prev.permissions.includes(permId)
                ? prev.permissions.filter(p => p !== permId)
                : [...prev.permissions, permId];
            return { ...prev, permissions: perms };
        });
    };

    if (loading && !users.length && !groups.length) return <div className="loading"><Loader className="spin" /> Loading...</div>;

    return (
        <div className="users-groups-page">
            <UserModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={
                    modalMode === 'add'
                        ? (modalType === 'user' ? 'Add New User' : 'Create Group')
                        : (modalType === 'user' ? 'Edit User' : 'Edit Group')
                }
            >
                <form onSubmit={handleSubmit} className="user-form">
                    {modalType === 'user' ? (
                        <>
                            <div className="form-group">
                                <label>Name</label>
                                <input type="text" required value={userFormData.name} onChange={e => setUserFormData({ ...userFormData, name: e.target.value })} />
                            </div>
                            {modalMode === 'add' && (
                                <>
                                    <div className="form-group">
                                        <label>Email</label>
                                        <input type="email" required value={userFormData.email} onChange={e => setUserFormData({ ...userFormData, email: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label>Password</label>
                                        <input type="password" required value={userFormData.password} onChange={e => setUserFormData({ ...userFormData, password: e.target.value })} />
                                    </div>
                                </>
                            )}
                            <div className="form-group">
                                <label>Role</label>
                                <select value={userFormData.role} onChange={e => setUserFormData({ ...userFormData, role: e.target.value })}>
                                    <option value="viewer">Viewer</option>
                                    <option value="developer">Developer</option>
                                    <option value="admin">Admin</option>
                                </select>
                                <p className="form-guide-text">Determines system-wide access level.</p>
                            </div>

                            <div className="form-group">
                                <label>Assign Groups</label>
                                <div className="groups-selection-list">
                                    {groups.length === 0 && <p style={{ padding: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No groups available</p>}
                                    {groups.map(group => (
                                        <label key={group.id} className="group-selection-item">
                                            <input
                                                type="checkbox"
                                                checked={userFormData.group_ids?.includes(group.id) || false}
                                                onChange={(e) => {
                                                    const newGroups = e.target.checked
                                                        ? [...(userFormData.group_ids || []), group.id]
                                                        : (userFormData.group_ids || []).filter(id => id !== group.id);
                                                    setUserFormData({ ...userFormData, group_ids: newGroups });
                                                }}
                                            />
                                            {group.name}
                                        </label>
                                    ))}
                                </div>
                                <p className="form-guide-text">Grant specific granular permissions via groups.</p>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="form-group">
                                <label>Group Name</label>
                                <input type="text" required value={groupFormData.name} onChange={e => setGroupFormData({ ...groupFormData, name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <input type="text" value={groupFormData.description} onChange={e => setGroupFormData({ ...groupFormData, description: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Permissions</label>
                                <div className="permissions-list">
                                    {AVAILABLE_PERMISSIONS.map(perm => (
                                        <label key={perm.id} className="permission-item">
                                            <input
                                                type="checkbox"
                                                checked={groupFormData.permissions.includes(perm.id)}
                                                onChange={() => togglePermission(perm.id)}
                                            />
                                            {perm.label}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    <div className="modal-actions">
                        <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>Cancel</button>
                        <button type="submit" className="btn-primary">
                            {modalMode === 'add' ? 'Create' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </UserModal>

            <div className="page-header">
                <div>
                    <h1>Users & Groups</h1>
                    <p>Manage user access and permissions</p>
                </div>
                {isAdmin && (
                    <button className="btn-primary" onClick={activeTab === 'users' ? handleOpenAddUser : handleOpenAddGroup}>
                        <Plus size={16} />
                        {activeTab === 'users' ? 'Add User' : 'Create Group'}
                    </button>
                )}
            </div>

            <div className="tabs">
                <button className={`tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
                    <Users size={18} /> Users
                </button>
                <button className={`tab ${activeTab === 'groups' ? 'active' : ''}`} onClick={() => setActiveTab('groups')}>
                    <Shield size={18} /> Groups
                </button>
            </div>

            <div className="search-bar">
                <Search size={18} />
                <input
                    type="text"
                    placeholder={`Search ${activeTab}...`}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {error && <div className="error-message">{error}</div>}

            {activeTab === 'users' ? (
                <div className="users-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Last Login</th>
                                {isAdmin && <th>Actions</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {filteredUsers.map(user => (
                                <tr key={user.id}>
                                    <td className="user-name">{user.name}</td>
                                    <td className="user-email">{user.email}</td>
                                    <td><span className={`role-badge ${getRoleBadgeClass(user.role)}`}>{user.role}</span></td>
                                    <td><span className={`status-indicator ${user.status?.toLowerCase()}`}>{user.status}</span></td>
                                    <td className="last-login">{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                                    {isAdmin && (
                                        <td>
                                            <div className="action-buttons">
                                                <button className="btn-tiny" onClick={() => handleEditUser(user)}>Edit</button>
                                                {user.id !== JSON.parse(localStorage.getItem('user') || '{}').id && (
                                                    <button className="btn-tiny danger" onClick={() => handleDeleteUser(user.id)}>Delete</button>
                                                )}
                                            </div>
                                        </td>
                                    )}
                                </tr>
                            ))}
                            {filteredUsers.length === 0 && <tr><td colSpan="6" className="no-results">No users found</td></tr>}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="groups-grid">
                    {filteredGroups.map(group => (
                        <div key={group.id} className="group-card">
                            <div className="group-header">
                                <Shield size={24} />
                                <h3>{group.name}</h3>
                            </div>
                            <p className="group-description">{group.description}</p>
                            <div className="group-stats">
                                <div className="stat">
                                    <span className="stat-value">{group.member_count}</span>
                                    <span className="stat-label">Members</span>
                                </div>
                                <div className="stat">
                                    <span className="stat-value">{group.permissions.length}</span>
                                    <span className="stat-label">Permissions</span>
                                </div>
                            </div>
                            <div className="group-permissions">
                                {group.permissions.slice(0, 3).map((perm, i) => (
                                    <span key={i} className="permission-tag">{perm}</span>
                                ))}
                                {group.permissions.length > 3 && <span className="permission-tag more">+{group.permissions.length - 3}</span>}
                            </div>
                            {isAdmin && (
                                <div className="card-actions" style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                                    <button className="btn-tiny" onClick={() => handleEditGroup(group)}>Edit</button>
                                    <button className="btn-tiny danger" onClick={() => handleDeleteGroup(group.id)}>Delete</button>
                                </div>
                            )}
                        </div>
                    ))}
                    {filteredGroups.length === 0 && <p className="no-results">No groups found</p>}
                </div>
            )}
        </div>
    );
};

// Also verify UserModal component existence (it was inside the component in previous view)
// I need to include UserModal definition inside or outside. 
// The previous view had UserModal defined INSIDE UsersGroups (line 74). 
// I should keep it or redefine it. 
// To be safe and clean, I will define it outside.

const UserModal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;
    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <div className="modal-header">
                    <h3>{title}</h3>
                    <button className="btn-close" onClick={onClose}>&times;</button>
                </div>
                <div className="modal-body">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default UsersGroups;
