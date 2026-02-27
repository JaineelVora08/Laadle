import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * Navbar — props: { user: UserProfileResponse }
 */
export default function Navbar({ user }) {
    const logout = useAuthStore((state) => state.logout);
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <nav style={{ display: 'flex', gap: 16, padding: '12px 24px', background: '#222', color: '#fff', alignItems: 'center' }}>
            <Link to="/" style={{ color: '#fff', textDecoration: 'none', fontWeight: 'bold' }}>BEACON</Link>
            {user ? (
                <>
                    <Link to="/profile" style={{ color: '#ccc' }}>Profile</Link>
                    <Link to={user.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student'} style={{ color: '#ccc' }}>Dashboard</Link>
                    <span style={{ marginLeft: 'auto', color: '#aaa' }}>{user.name} ({user.role})</span>
                    <button onClick={handleLogout} style={{ marginLeft: 8 }}>Logout</button>
                </>
            ) : (
                <>
                    <Link to="/login" style={{ color: '#ccc', marginLeft: 'auto' }}>Login</Link>
                    <Link to="/register" style={{ color: '#ccc' }}>Register</Link>
                </>
            )}
        </nav>
    );
}
