import React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * RegisterPage — renders register form, calls api/auth.register()
 */
export default function RegisterPage() {
    const navigate = useNavigate();
    const register = useAuthStore((state) => state.register);

    const [form, setForm] = useState({
        name: '',
        email: '',
        password: '',
        role: 'STUDENT',
        current_level: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await register(form);
            navigate(data.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student');
        } catch (err) {
            setError(err?.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 420, margin: '2rem auto' }}>
            <h2>Register</h2>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    placeholder="Full name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                    required
                />
                <input
                    type="email"
                    placeholder="College email (@iitj.ac.in)"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                    required
                />
                <select
                    value={form.role}
                    onChange={(e) => setForm({ ...form, role: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                >
                    <option value="STUDENT">Student</option>
                    <option value="SENIOR">Senior</option>
                </select>
                <input
                    type="text"
                    placeholder="Current level (optional)"
                    value={form.current_level}
                    onChange={(e) => setForm({ ...form, current_level: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                />
                <button type="submit" disabled={loading}>Create Account</button>
            </form>
            {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
        </div>
    );
}
