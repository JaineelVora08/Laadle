import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * PeerCard - displays a similar junior match by shared domains.
 */
export default function PeerCard({ peer }) {
    const navigate = useNavigate();
    const rawSimilarity = Number(peer?.similarity_score || 0);
    const score = rawSimilarity > 0 ? Math.max(1, Math.round(rawSimilarity * 100)) : 0;

    return (
        <div className="glass-card" style={{ padding: 20, marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: 18, color: 'var(--text-heading)' }}>{peer?.name || 'Student'}</h3>
                    <p style={{ margin: '6px 0', color: 'var(--text-secondary)', fontSize: 14 }}>
                        Level: {peer?.current_level || 'beginner'}
                    </p>
                    <p style={{ margin: '6px 0', color: 'var(--text-secondary)', fontSize: 13 }}>
                        Shared domains: {peer?.shared_domain_count || 0}
                    </p>
                </div>
                <div
                    style={{
                        padding: '6px 10px',
                        borderRadius: 999,
                        fontSize: 12,
                        fontWeight: 700,
                        color: '#67e8f9',
                        border: '1px solid rgba(103, 232, 249, 0.35)',
                        background: 'rgba(103, 232, 249, 0.12)',
                    }}
                >
                    {score}% match
                </div>
            </div>

            {Array.isArray(peer?.shared_domains) && peer.shared_domains.length > 0 && (
                <p style={{ marginTop: 10, marginBottom: 0, color: 'var(--text-secondary)', fontSize: 13 }}>
                    {peer.shared_domains.join(' | ')}
                </p>
            )}

            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                    onClick={() => navigate(`/profile/${peer.student_id}`)}
                    className="btn-ghost"
                >
                    View Profile
                </button>
            </div>
        </div>
    );
}
