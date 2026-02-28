import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { getSeniorPendingQueries } from '../api/query';
import TrustScoreBadge from '../components/TrustScoreBadge';

/**
 * SeniorDashboard — shows stats, trust score, quick links.
 */
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
        <div style={{ maxWidth: 800, margin: '2rem auto', padding: '0 16px' }}>
            <h2 style={{ marginBottom: 4 }}>Welcome, {user?.name || 'Senior'} 🌟</h2>
            <p style={{ color: '#6b7280', marginTop: 0 }}>Senior mentor dashboard</p>

            {/* Trust Score */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 20 }}>
                <TrustScoreBadge score={user?.trust_score} />
                <div>
                    <p style={{ margin: 0, fontWeight: 600 }}>Your Trust Score</p>
                    <p style={{ margin: 0, color: '#6b7280', fontSize: 13 }}>
                        Based on feedback, consistency, and achievements
                    </p>
                </div>
            </div>

            {/* Stats */}
            <div
                style={{
                    display: 'flex',
                    gap: 16,
                    marginTop: 24,
                    flexWrap: 'wrap',
                }}
            >
                <div
                    style={{
                        flex: 1,
                        minWidth: 150,
                        padding: 20,
                        borderRadius: 12,
                        background: '#fef3c7',
                        textAlign: 'center',
                    }}
                >
                    <p style={{ margin: 0, fontSize: 28, fontWeight: 700, color: '#92400e' }}>
                        {loading ? '...' : pendingCount}
                    </p>
                    <p style={{ margin: '4px 0 0', color: '#92400e', fontSize: 14 }}>Pending Queries</p>
                </div>
                <div
                    style={{
                        flex: 1,
                        minWidth: 150,
                        padding: 20,
                        borderRadius: 12,
                        background: '#dbeafe',
                        textAlign: 'center',
                    }}
                >
                    <p style={{ margin: 0, fontSize: 28, fontWeight: 700, color: '#1e40af' }}>
                        {user?.active_load ?? 0}
                    </p>
                    <p style={{ margin: '4px 0 0', color: '#1e40af', fontSize: 14 }}>Active Mentorships</p>
                </div>
            </div>

            {/* Quick Links */}
            <div style={{ marginTop: 32, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Link
                    to="/inbox"
                    style={{
                        padding: '12px 24px',
                        borderRadius: 10,
                        background: '#fef3c7',
                        color: '#92400e',
                        textDecoration: 'none',
                        fontWeight: 600,
                        fontSize: 14,
                    }}
                >
                    📥 View Inbox
                </Link>
                <Link
                    to="/messages"
                    style={{
                        padding: '12px 24px',
                        borderRadius: 10,
                        background: '#dbeafe',
                        color: '#1e40af',
                        textDecoration: 'none',
                        fontWeight: 600,
                        fontSize: 14,
                    }}
                >
                    💬 Messages
                </Link>
                <Link
                    to="/profile"
                    style={{
                        padding: '12px 24px',
                        borderRadius: 10,
                        background: '#ede9fe',
                        color: '#7c3aed',
                        textDecoration: 'none',
                        fontWeight: 600,
                        fontSize: 14,
                    }}
                >
                    👤 My Profile
                </Link>
            </div>
        </div>
    );
}
