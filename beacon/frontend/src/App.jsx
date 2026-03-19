import React from 'react';
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import AuthPage from './pages/AuthPage';
import StudentDashboard from './pages/StudentDashboard';
import SeniorDashboard from './pages/SeniorDashboard';
import ProfilePage from './pages/ProfilePage';
import MentorMatchPage from './pages/MentorMatchPage';
import QueryPage from './pages/QueryPage';
import SeniorInboxPage from './pages/SeniorInboxPage';
import MessagingPage from './pages/MessagingPage';
import SeniorOnboardingPage from './pages/SeniorOnboardingPage';
import { useAuthStore } from './store/authStore';

/**
 * ProtectedRoute wrapper — checks auth token and role access.
 */
function ProtectedRoute({ children, requiredRole }) {
    const token = useAuthStore((state) => state.token);
    const role = useAuthStore((state) => state.role);

    if (!token) {
        return <Navigate to="/login" replace />;
    }
    if (requiredRole && role !== requiredRole) {
        return <Navigate to={role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student'} replace />;
    }
    return children;
}

/**
 * Layout — conditionally renders Navbar (hidden on auth pages).
 */
function Layout({ user, children }) {
    const { pathname } = useLocation();
    const hideNavbar = pathname === '/login' || pathname === '/register' || pathname === '/onboarding/senior';

    return (
        <>
            {!hideNavbar && <Navbar user={user} />}
            {children}
        </>
    );
}

/**
 * Root application component.
 * Sets up routing for all pages.
 */
export default function App() {
    const user = useAuthStore((state) => state.user);
    const userId = useAuthStore((state) => state.userId);
    const token = useAuthStore((state) => state.token);
    const role = useAuthStore((state) => state.role);
    const profileCompleted = useAuthStore((state) => state.profileCompleted);
    const hydrateProfile = useAuthStore((state) => state.hydrateProfile);

    useEffect(() => {
        if (userId && !user) {
            hydrateProfile();
        }
    }, [userId, user, hydrateProfile]);

    return (
        <BrowserRouter>
            <Layout user={user}>
                <Routes>
                    {/* Public root — redirect based on auth state */}
                    <Route
                        path="/"
                        element={
                            token
                                ? (role === 'SENIOR' && profileCompleted === false
                                    ? <Navigate to="/onboarding/senior" replace />
                                    : <Navigate to={role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student'} replace />)
                                : <Navigate to="/login" replace />
                        }
                    />

                    {/* Auth pages */}
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/register" element={<AuthPage />} />

                    {/* Senior onboarding (profile not yet completed) */}
                    <Route path="/onboarding/senior" element={
                        <ProtectedRoute requiredRole="SENIOR"><SeniorOnboardingPage /></ProtectedRoute>
                    } />

                    {/* Dashboard — role-specific */}
                    <Route path="/dashboard/student" element={
                        <ProtectedRoute requiredRole="STUDENT"><StudentDashboard /></ProtectedRoute>
                    } />
                    <Route path="/dashboard/senior" element={
                        <ProtectedRoute requiredRole="SENIOR"><SeniorDashboard /></ProtectedRoute>
                    } />

                    {/* Shared route with dynamic userId support */}
                    <Route path="/profile/:userId?" element={
                        <ProtectedRoute><ProfilePage /></ProtectedRoute>
                    } />

                    {/* Student-only */}
                    <Route path="/mentor-match" element={
                        <ProtectedRoute requiredRole="STUDENT"><MentorMatchPage /></ProtectedRoute>
                    } />
                    <Route path="/query" element={
                        <ProtectedRoute requiredRole="STUDENT"><QueryPage /></ProtectedRoute>
                    } />

                    {/* Senior-only */}
                    <Route path="/inbox" element={
                        <ProtectedRoute requiredRole="SENIOR"><SeniorInboxPage /></ProtectedRoute>
                    } />

                    {/* Both roles */}
                    <Route path="/messages" element={
                        <ProtectedRoute><MessagingPage /></ProtectedRoute>
                    } />
                </Routes>
            </Layout>
        </BrowserRouter>
    );
}

