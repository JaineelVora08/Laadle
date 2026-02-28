import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * Navbar — role-based navigation links with logout.
 * Reads auth state directly from store.
 */
export default function Navbar({ user }) {
    const logout = useAuthStore((state) => state.logout);
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const linkStyle = {
        color: '#d1d5db',
        textDecoration: 'none',
        padding: '4px 10px',
        borderRadius: 6,
        fontSize: 14,
        transition: 'color 0.15s',
    };

    return (
        <nav
            style={{
                display: 'flex',
                gap: 12,
                padding: '10px 24px',
                background: 'linear-gradient(135deg, #1e1b4b, #312e81)',
                color: '#fff',
                alignItems: 'center',
                boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
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
                    letterSpacing: 1,
                    marginRight: 8,
                }}
            >
                🔆 BEACON
            </Link>

            {user ? (
                <>
                    {/* Role-based links */}
                    {user.role === 'STUDENT' ? (
                        <>
                            <Link to="/dashboard/student" style={linkStyle}>Dashboard</Link>
                            <Link to="/mentor-match" style={linkStyle}>Find Mentor</Link>
                            <Link to="/query" style={linkStyle}>Ask Query</Link>
                            <Link to="/messages" style={linkStyle}>Messages</Link>
                        </>
                    ) : (
                        <>
                            <Link to="/dashboard/senior" style={linkStyle}>Dashboard</Link>
                            <Link to="/inbox" style={linkStyle}>Inbox</Link>
                            <Link to="/messages" style={linkStyle}>Messages</Link>
                        </>
                    )}

                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
                        <Link to="/profile" style={{ ...linkStyle, color: '#a5b4fc' }}>
                            {user.name}
                        </Link>
                        <span
                            style={{
                                padding: '2px 8px',
                                borderRadius: 9999,
                                fontSize: 11,
                                fontWeight: 700,
                                background: user.role === 'SENIOR' ? '#8b5cf6' : '#3b82f6',
                                color: '#fff',
                            }}
                        >
                            {user.role}
                        </span>
                        <button
                            onClick={handleLogout}
                            style={{
                                padding: '4px 14px',
                                borderRadius: 6,
                                border: '1px solid rgba(255,255,255,0.3)',
                                background: 'transparent',
                                color: '#e5e7eb',
                                cursor: 'pointer',
                                fontSize: 13,
                            }}
                        >
                            Logout
                        </button>
                    </div>
                </>
            ) : (
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                    <Link to="/login" style={linkStyle}>Login</Link>
                    <Link to="/register" style={linkStyle}>Register</Link>
                </div>
            )}
        </nav>
    );
}
