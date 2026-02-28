import React from 'react';
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import StudentDashboard from './pages/StudentDashboard';
import SeniorDashboard from './pages/SeniorDashboard';
import ProfilePage from './pages/ProfilePage';
import MentorMatchPage from './pages/MentorMatchPage';
import QueryPage from './pages/QueryPage';
import SeniorInboxPage from './pages/SeniorInboxPage';
import MessagingPage from './pages/MessagingPage';
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
 * Root application component.
 * Sets up routing for all pages.
 */
export default function App() {
    const user = useAuthStore((state) => state.user);
    const userId = useAuthStore((state) => state.userId);
    const token = useAuthStore((state) => state.token);
    const role = useAuthStore((state) => state.role);
    const hydrateProfile = useAuthStore((state) => state.hydrateProfile);

    useEffect(() => {
        if (userId && !user) {
            hydrateProfile();
        }
    }, [userId, user, hydrateProfile]);

    return (
        <BrowserRouter>
            <Navbar user={user} />
            <Routes>
                {/* Public root — redirect based on auth state */}
                <Route
                    path="/"
                    element={
                        token
                            ? <Navigate to={role === 'SENIOR' ? '/dashboard/senior' : '/dashboard/student'} replace />
                            : <Navigate to="/login" replace />
                    }
                />

                {/* Auth pages */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

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
        </BrowserRouter>
    );
}
