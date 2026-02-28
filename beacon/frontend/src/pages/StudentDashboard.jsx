import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useQueryStore } from '../store/queryStore';
import { getUserDomains, addDomain } from '../api/domains';
import DomainBadge from '../components/DomainBadge';
import QueryCard from '../components/QueryCard';

/**
 * StudentDashboard — shows domains, quick links, recent queries.
 */
export default function StudentDashboard() {
    const user = useAuthStore((s) => s.user);
    const userId = useAuthStore((s) => s.userId);
    const queries = useQueryStore((s) => s.queries);

    const [domains, setDomains] = useState([]);
    const [newDomain, setNewDomain] = useState('');
    const [loading, setLoading] = useState(true);
    const [addingDomain, setAddingDomain] = useState(false);

    useEffect(() => {
        if (!userId) return;
        setLoading(true);
        getUserDomains(userId)
            .then((data) => setDomains(Array.isArray(data) ? data : []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [userId]);

    const handleAddDomain = async (e) => {
        e.preventDefault();
        if (!newDomain.trim() || !userId) return;
        setAddingDomain(true);
        try {
            const result = await addDomain({ user_id: userId, raw_interest_text: newDomain.trim() });
            setDomains((prev) => [...prev, result]);
            setNewDomain('');
        } catch {
            // silently fail
        } finally {
            setAddingDomain(false);
        }
    };

    const recentQueries = queries.slice(-3).reverse();

    return (
        <div style={{ maxWidth: 800, margin: '2rem auto', padding: '0 16px' }}>
            <h2 style={{ marginBottom: 4 }}>Welcome, {user?.name || 'Student'} 👋</h2>
            <p style={{ color: '#6b7280', marginTop: 0 }}>Here's your dashboard overview.</p>

            {/* Domains */}
            <div style={{ marginTop: 24 }}>
                <h3>Your Domains</h3>
                {loading ? (
                    <p style={{ color: '#9ca3af' }}>Loading domains...</p>
                ) : domains.length === 0 ? (
                    <p style={{ color: '#9ca3af' }}>No domains yet. Add one below!</p>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {domains.map((d) => (
                            <DomainBadge key={d.domain_id} domain={d} />
                        ))}
                    </div>
                )}
                <form onSubmit={handleAddDomain} style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                    <input
                        type="text"
                        placeholder="Add a domain (e.g. Machine Learning)"
                        value={newDomain}
                        onChange={(e) => setNewDomain(e.target.value)}
                        style={{
                            flex: 1,
                            padding: '8px 12px',
                            borderRadius: 8,
                            border: '1px solid #d1d5db',
                            fontSize: 14,
                        }}
                    />
                    <button
                        type="submit"
                        disabled={addingDomain || !newDomain.trim()}
                        style={{
                            padding: '8px 16px',
                            borderRadius: 8,
                            border: 'none',
                            background: '#3b82f6',
                            color: '#fff',
                            cursor: 'pointer',
                            fontSize: 14,
                        }}
                    >
                        {addingDomain ? 'Adding...' : 'Add'}
                    </button>
                </form>
            </div>

            {/* Quick Links */}
            <div style={{ marginTop: 32, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Link
                    to="/mentor-match"
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
                    🎯 Find a Mentor
                </Link>
                <Link
                    to="/query"
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
                    ❓ Ask a Question
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
            </div>

            {/* Recent Queries */}
            {recentQueries.length > 0 && (
                <div style={{ marginTop: 32 }}>
                    <h3>Recent Queries</h3>
                    {recentQueries.map((q) => (
                        <QueryCard key={q.query_id} query={q} />
                    ))}
                </div>
            )}
        </div>
    );
}
