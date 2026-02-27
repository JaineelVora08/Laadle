import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import StudentDashboard from './pages/StudentDashboard';
import SeniorDashboard from './pages/SeniorDashboard';
import ProfilePage from './pages/ProfilePage';
import MentorMatchPage from './pages/MentorMatchPage';
import QueryPage from './pages/QueryPage';
import SeniorInboxPage from './pages/SeniorInboxPage';

/**
 * Root application component.
 * Sets up routing for all pages.
 */
export default function App() {
    return (
        <BrowserRouter>
            <Navbar user={null} />
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/dashboard/student" element={<StudentDashboard />} />
                <Route path="/dashboard/senior" element={<SeniorDashboard />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/mentor-match" element={<MentorMatchPage />} />
                <Route path="/query" element={<QueryPage />} />
                <Route path="/inbox" element={<SeniorInboxPage />} />
            </Routes>
        </BrowserRouter>
    );
}
