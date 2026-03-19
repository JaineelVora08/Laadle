import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * Navbar — dark glassmorphism navbar with role-based links.
 */
export default function Navbar({ user }) {
    const logout = useAuthStore((state) => state.logout);
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <nav
            style={{
                display: 'flex',
                gap: 12,
                padding: '12px 28px',
                background: 'rgba(10, 10, 10, 0.85)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                color: '#fff',
                alignItems: 'center',
                position: 'sticky',
                top: 0,
                zIndex: 100,
            }}
        >
            <Link
                to="/"
                style={{
                    color: '#fff',
                    textDecoration: 'none',
                    fontWeight: 800,
                    fontSize: 18,
                    letterSpacing: 2,
                    marginRight: 12,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                }}
            >
                <span
                    style={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background: '#00b4d8',
                        boxShadow: '0 0 8px rgba(0,180,216,0.5)',
                        display: 'inline-block',
                    }}
                />
                BEACON
            </Link>

            {user ? (
                <>
                    {user.role === 'STUDENT' ? (
                        <>
                            <NavLink to="/dashboard/student">Dashboard</NavLink>
                            <NavLink to="/mentor-match">Find Matches</NavLink>
                            <NavLink to="/query">Ask Query</NavLink>
                            <NavLink to="/messages">Messages</NavLink>
                        </>
                    ) : (
                        <>
                            <NavLink to="/dashboard/senior">Dashboard</NavLink>
                            <NavLink to="/inbox">Inbox</NavLink>
                            <NavLink to="/messages">Messages</NavLink>
                        </>
                    )}

                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 14 }}>
                        <Link
                            to="/profile"
                            style={{
                                color: '#ccc',
                                textDecoration: 'none',
                                fontSize: 14,
                                fontWeight: 500,
                                transition: 'color 0.2s',
                            }}
                        >
                            {user.name}
                        </Link>
                        <span
                            style={{
                                padding: '3px 10px',
                                borderRadius: 9999,
                                fontSize: 11,
                                fontWeight: 700,
                                background: 'rgba(0, 180, 216, 0.12)',
                                color: '#00b4d8',
                                border: '1px solid rgba(0, 180, 216, 0.2)',
                            }}
                        >
                            {user.role}
                        </span>
                        <button
                            onClick={handleLogout}
                            style={{
                                padding: '5px 16px',
                                borderRadius: 8,
                                border: '1px solid rgba(255,255,255,0.1)',
                                background: 'transparent',
                                color: '#999',
                                cursor: 'pointer',
                                fontSize: 13,
                                transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.borderColor = 'rgba(239,68,68,0.4)';
                                e.target.style.color = '#ef4444';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.borderColor = 'rgba(255,255,255,0.1)';
                                e.target.style.color = '#999';
                            }}
                        >
                            Logout
                        </button>
                    </div>
                </>
            ) : (
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                    <NavLink to="/login">Login</NavLink>
                    <NavLink to="/register">Register</NavLink>
                </div>
            )}
        </nav>
    );
}

function NavLink({ to, children }) {
    return (
        <Link
            to={to}
            style={{
                color: '#999',
                textDecoration: 'none',
                padding: '5px 12px',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 500,
                transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
                e.target.style.color = '#00b4d8';
                e.target.style.background = 'rgba(0,180,216,0.06)';
            }}
            onMouseLeave={(e) => {
                e.target.style.color = '#999';
                e.target.style.background = 'transparent';
            }}
        >
            {children}
        </Link>
    );
}
