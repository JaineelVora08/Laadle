import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import './AuthPage.css';

/**
 * AuthPage — combined sliding Login / Register page.
 * Register form on the left, Login form on the right.
 * A dark overlay panel slides between them.
 */
export default function AuthPage() {
    const navigate = useNavigate();
    const location = useLocation();

    const login = useAuthStore((s) => s.login);
    const register = useAuthStore((s) => s.register);
    const googleLogin = useAuthStore((s) => s.googleLogin);

    // Determine initial panel from URL
    const [isLoginActive, setIsLoginActive] = useState(location.pathname === '/login');

    // ---- Login form state ----
    const [loginForm, setLoginForm] = useState({ email: '', password: '' });
    const [loginError, setLoginError] = useState('');
    const [loginLoading, setLoginLoading] = useState(false);
    const googleButtonRef = useRef(null);

    // ---- Register form state ----
    const [regForm, setRegForm] = useState({
        name: '',
        email: '',
        password: '',
        role: 'STUDENT',
        current_level: '',
    });
    const [regError, setRegError] = useState('');
    const [regLoading, setRegLoading] = useState(false);

    // ---- Helper: extract error messages ----
    const getErrorMessage = (err, fallback) => {
        const d = err?.response?.data;
        if (!d) return fallback;
        if (Array.isArray(d) && typeof d[0] === 'string') return d[0];
        if (typeof d.detail === 'string') return d.detail;
        if (typeof d.non_field_errors?.[0] === 'string') return d.non_field_errors[0];
        const first = Object.values(d).find((v) => Array.isArray(v) && typeof v[0] === 'string');
        if (first) return first[0];
        return fallback;
    };

    // ---- Google Identity Services ----
    useEffect(() => {
        const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
        if (!clientId) return;

        const handleCredentialResponse = async (response) => {
            setLoginError('');
            setLoginLoading(true);
            try {
                const data = await googleLogin({ id_token: response.credential });
                if (data.role === 'SENIOR' && !data.profile_completed) {
                    navigate('/onboarding/senior');
                } else {
                    navigate(data.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student');
                }
            } catch (err) {
                const msg = getErrorMessage(err, 'Google login failed');
                if (msg.toLowerCase().includes('register')) {
                    setLoginError('No account found. Switching to registration...');
                    setTimeout(() => setIsLoginActive(false), 1500);
                } else {
                    setLoginError(msg);
                }
            } finally {
                setLoginLoading(false);
            }
        };

        const initializeGoogle = () => {
            if (!window.google || !googleButtonRef.current) return;

            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: handleCredentialResponse,
                auto_select: false,
            });

            window.google.accounts.id.renderButton(googleButtonRef.current, {
                type: 'standard',
                theme: 'filled_black',
                size: 'large',
                text: 'signin_with',
                shape: 'pill',
            });
        };

        if (window.google?.accounts) {
            initializeGoogle();
            return;
        }

        const existing = document.getElementById('google-identity-script');
        if (existing) {
            existing.addEventListener('load', initializeGoogle);
            return () => existing.removeEventListener('load', initializeGoogle);
        }

        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.id = 'google-identity-script';
        script.onload = initializeGoogle;
        document.body.appendChild(script);

        return () => { script.onload = null; };
    }, [googleLogin, navigate]);

    // ---- Re-render Google button when switching to login ----
    useEffect(() => {
        if (!isLoginActive) return;
        const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
        if (!clientId || !window.google?.accounts || !googleButtonRef.current) return;

        // Small delay to let the DOM settle after the slide animation
        const t = setTimeout(() => {
            if (!googleButtonRef.current) return;
            googleButtonRef.current.innerHTML = '';
            window.google.accounts.id.renderButton(googleButtonRef.current, {
                type: 'standard',
                theme: 'filled_black',
                size: 'large',
                text: 'signin_with',
                shape: 'pill',
            });
        }, 650);

        return () => clearTimeout(t);
    }, [isLoginActive]);

    // ---- Handlers ----
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoginError('');
        setLoginLoading(true);
        try {
            const data = await login(loginForm);
            if (data.role === 'SENIOR' && !data.profile_completed) {
                navigate('/onboarding/senior');
            } else {
                navigate(data.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student');
            }
        } catch (err) {
            setLoginError(getErrorMessage(err, 'Login failed'));
        } finally {
            setLoginLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setRegError('');
        setRegLoading(true);
        try {
            const data = await register(regForm);
            if (data.role === 'SENIOR' && !data.profile_completed) {
                navigate('/onboarding/senior');
            } else {
                navigate(data.role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student');
            }
        } catch (err) {
            setRegError(getErrorMessage(err, 'Registration failed'));
        } finally {
            setRegLoading(false);
        }
    };

    const togglePanel = (toLogin) => {
        setIsLoginActive(toLogin);
        // Update URL without reloading
        window.history.replaceState(null, '', toLogin ? '/login' : '/register');
    };

    // ---- Render ----
    return (
        <div className="auth-page">
            {/* Brand */}
            <div className="auth-brand">
                <span className="auth-brand-dot" />
                <span className="auth-brand-name">Beacon</span>
            </div>

            <div className={`auth-container ${isLoginActive ? 'login-active' : 'register-active'}`}>

                {/* ====== REGISTER FORM (left side) ====== */}
                <div className="auth-form-container register-form">
                    <form className="auth-form" onSubmit={handleRegister}>
                        <h2>Create Account</h2>
                        <p className="auth-subtitle">Join the BEACON community</p>

                        <div className="auth-input-group">
                            <input
                                type="text"
                                placeholder="Full name"
                                value={regForm.name}
                                onChange={(e) => setRegForm({ ...regForm, name: e.target.value })}
                                required
                            />
                        </div>
                        <div className="auth-input-group">
                            <input
                                type="email"
                                placeholder="College email (@iitj.ac.in)"
                                value={regForm.email}
                                onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                                required
                            />
                        </div>
                        <div className="auth-input-group">
                            <input
                                type="password"
                                placeholder="Password"
                                value={regForm.password}
                                onChange={(e) => setRegForm({ ...regForm, password: e.target.value })}
                                required
                            />
                        </div>
                        <div className="auth-input-group">
                            <select
                                value={regForm.role}
                                onChange={(e) => setRegForm({ ...regForm, role: e.target.value })}
                            >
                                <option value="STUDENT">Student</option>
                                <option value="SENIOR">Senior</option>
                            </select>
                        </div>
                        <div className="auth-input-group">
                            <input
                                type="text"
                                placeholder="Current level (optional)"
                                value={regForm.current_level}
                                onChange={(e) => setRegForm({ ...regForm, current_level: e.target.value })}
                            />
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={regLoading}>
                            {regLoading ? 'Creating...' : 'Create Account'}
                        </button>

                        {regError && <p className="auth-error">{regError}</p>}
                    </form>
                </div>

                {/* ====== LOGIN FORM (right side) ====== */}
                <div className="auth-form-container login-form">
                    <form className="auth-form" onSubmit={handleLogin}>
                        <h2>Welcome Back</h2>
                        <p className="auth-subtitle">Sign in to your account</p>

                        <div className="auth-input-group">
                            <input
                                type="email"
                                placeholder="College email (@iitj.ac.in)"
                                value={loginForm.email}
                                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                                required
                            />
                        </div>
                        <div className="auth-input-group">
                            <input
                                type="password"
                                placeholder="Password"
                                value={loginForm.password}
                                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                                required
                            />
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={loginLoading}>
                            {loginLoading ? 'Signing in...' : 'Sign In'}
                        </button>

                        {loginError && <p className="auth-error">{loginError}</p>}

                        <div className="auth-divider">or</div>

                        <div className="auth-google-container">
                            <div ref={googleButtonRef} />
                            {!import.meta.env.VITE_GOOGLE_CLIENT_ID && (
                                <p style={{ color: '#ef4444', fontSize: '0.75rem' }}>
                                    Set VITE_GOOGLE_CLIENT_ID to enable Google sign-in.
                                </p>
                            )}
                        </div>
                    </form>
                </div>

                {/* ====== SLIDING OVERLAY ====== */}
                <div className="auth-overlay">
                    <div className="auth-overlay-inner">
                        {isLoginActive ? (
                            <>
                                <h2>New Here?</h2>
                                <p>Create an account and start your journey with BEACON today.</p>
                                <button
                                    type="button"
                                    className="auth-toggle-btn"
                                    onClick={() => togglePanel(false)}
                                >
                                    Register
                                </button>
                            </>
                        ) : (
                            <>
                                <h2>Welcome Back!</h2>
                                <p>Already have an account? Sign in to continue where you left off.</p>
                                <button
                                    type="button"
                                    className="auth-toggle-btn"
                                    onClick={() => togglePanel(true)}
                                >
                                    Login
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* ====== MOBILE TOGGLE (visible <768px) ====== */}
                <div className="mobile-toggle">
                    {isLoginActive ? (
                        <span>
                            Don't have an account?{' '}
                            <a onClick={() => togglePanel(false)}>Register</a>
                        </span>
                    ) : (
                        <span>
                            Already have an account?{' '}
                            <a onClick={() => togglePanel(true)}>Login</a>
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
