import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { getSeniorPendingQueries } from '../api/query';
import EffectsLayout from '../components/EffectsLayout';

export default function SeniorDashboard() {
    const user = useAuthStore((s) => s.user);
    const userId = useAuthStore((s) => s.userId);
    const [pendingCount, setPendingCount] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!userId) return;
        setLoading(true);
        getSeniorPendingQueries(userId)
            .then((data) => setPendingCount(Array.isArray(data) ? data.length : 0))
            .catch(() => setPendingCount(0))
            .finally(() => setLoading(false));
    }, [userId]);

    return (
        <EffectsLayout
            title={`Welcome, ${user?.name || 'Senior'} 🌟`}
            tagline="Senior mentor dashboard"
            auroraColors={["#00b4d8", "#0077b6", "#023e8a"]}
        >
            {/* Stats */}
            <div className="fx-reveal" style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
                <div className="fx-glass" style={{ flex: 1, minWidth: 150, textAlign: 'center', padding: 24 }}>
                    <p style={{ fontSize: '2rem', fontWeight: 800, color: '#00b4d8', margin: 0, textShadow: '0 0 20px rgba(0,180,216,0.3)' }}>
                        {loading ? '...' : pendingCount}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: '#666', margin: '6px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>
                        Pending Queries
                    </p>
                </div>
                <div className="fx-glass" style={{ flex: 1, minWidth: 150, textAlign: 'center', padding: 24 }}>
                    <p style={{ fontSize: '2rem', fontWeight: 800, color: '#00b4d8', margin: 0, textShadow: '0 0 20px rgba(0,180,216,0.3)' }}>
                        {user?.active_load ?? 0}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: '#666', margin: '6px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>
                        Active Mentorships
                    </p>
                </div>
            </div>

            {/* Quick Links */}
            <h3 className="fx-section-title">Quick Actions</h3>
            <div className="fx-reveal" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Link to="/inbox" className="quick-link" style={{ flex: 1 }}>📥 View Inbox</Link>
                <Link to="/messages" className="quick-link" style={{ flex: 1 }}>💬 Messages</Link>
                <Link to="/profile" className="quick-link" style={{ flex: 1 }}>👤 My Profile</Link>
                <Link to="/profile" className="quick-link" style={{ flex: 1 }}>🎯 Manage Domains</Link>
            </div>
        </EffectsLayout>
    );
}
