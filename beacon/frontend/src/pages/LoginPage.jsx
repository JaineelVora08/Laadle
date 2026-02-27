import React from 'react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * LoginPage — renders login form, calls api/auth.login(), redirects by role
 */
export default function LoginPage() {
    const navigate = useNavigate();
    const login = useAuthStore((state) => state.login);
    const googleLogin = useAuthStore((state) => state.googleLogin);

    const [form, setForm] = useState({ email: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const googleButtonRef = useRef(null);

    const getErrorMessage = (err, fallbackMessage) => {
        const data = err?.response?.data;
        if (!data) {
            return fallbackMessage;
        }
        if (typeof data.detail === 'string') {
            return data.detail;
        }
        if (typeof data.non_field_errors?.[0] === 'string') {
            return data.non_field_errors[0];
        }
        const firstFieldError = Object.values(data).find((value) => Array.isArray(value) && typeof value[0] === 'string');
        if (firstFieldError) {
            return firstFieldError[0];
        }
        return fallbackMessage;
    };

    useEffect(() => {
        const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
        if (!clientId) {
            return;
        }

        const handleCredentialResponse = async (response) => {
            setError('');
            setLoading(true);
            try {
                const data = await googleLogin({ id_token: response.credential });
                navigate(data.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student');
            } catch (err) {
                setError(getErrorMessage(err, 'Google login failed'));
            } finally {
                setLoading(false);
            }
        };

        const initializeGoogle = () => {
            if (!window.google || !googleButtonRef.current) {
                return;
            }

            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: handleCredentialResponse,
                auto_select: false,
            });

            window.google.accounts.id.renderButton(googleButtonRef.current, {
                type: 'standard',
                theme: 'outline',
                size: 'large',
                text: 'signin_with',
                shape: 'rectangular',
            });

            window.google.accounts.id.prompt();
        };

        if (window.google && window.google.accounts) {
            initializeGoogle();
            return;
        }

        const existingScript = document.getElementById('google-identity-script');
        if (existingScript) {
            existingScript.addEventListener('load', initializeGoogle);
            return () => existingScript.removeEventListener('load', initializeGoogle);
        }

        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.id = 'google-identity-script';
        script.onload = initializeGoogle;
        document.body.appendChild(script);

        return () => {
            script.onload = null;
        };
    }, [googleLogin, navigate]);

    const handleLogin = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await login(form);
            navigate(data.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student');
        } catch (err) {
            setError(getErrorMessage(err, 'Login failed'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 420, margin: '2rem auto' }}>
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
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
                <button type="submit" disabled={loading}>Email Login</button>
            </form>

            <hr style={{ margin: '16px 0' }} />

            <div style={{ marginBottom: 12 }}>
                <p style={{ marginBottom: 8 }}>Sign in with Google (college account):</p>
                <div ref={googleButtonRef} />
                {!import.meta.env.VITE_GOOGLE_CLIENT_ID ? (
                    <p style={{ color: 'crimson' }}>Set VITE_GOOGLE_CLIENT_ID to enable Google sign-in.</p>
                ) : null}
            </div>

            {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
        </div>
    );
}
