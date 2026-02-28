import React from 'react';
import { sendMessageRequest } from '../api/messaging';
import { useAuthStore } from '../store/authStore';
import TrustScoreBadge from './TrustScoreBadge';

/**
 * ProfileCard — dark glass card with profile info.
 */
export default function ProfileCard({ user }) {
    const currentUser = useAuthStore((s) => s.user);
    const [msgStatus, setMsgStatus] = React.useState(null);

    if (!user) return null;

    const isOtherUser = currentUser && currentUser.user_id !== user.user_id;

    const handleMessage = async () => {
        try {
            await sendMessageRequest({
                student_id: currentUser.user_id,
                senior_id: user.user_id,
                preview_text: `Hi ${user.name}, I'd like to connect with you!`,
            });
            setMsgStatus('Message request sent ✓');
        } catch {
            setMsgStatus('Failed to send request');
        }
    };

    return (
        <div className="glass-card-static" style={{ padding: 24, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h2 style={{ margin: 0, color: 'var(--text-heading)' }}>{user.name}</h2>
                    <span className="badge badge-role" style={{ marginTop: 4 }}>
                        {user.role}
                    </span>
                    {user.current_level && (
                        <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)', fontSize: 14 }}>{user.current_level}</p>
                    )}
                </div>
                <TrustScoreBadge score={user.trust_score} />
            </div>

            <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className={`status-dot ${user.availability ? 'online' : 'offline'}`} />
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                    {user.availability ? 'Available' : 'Unavailable'}
                </span>
            </div>

            {user.achievements && user.achievements.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <h4 style={{ margin: '0 0 8px', color: 'var(--text-primary)' }}>Achievements</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {user.achievements
                            .filter((a) => a.verified)
                            .map((a) => (
                                <div
                                    key={a.id}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        padding: '8px 12px',
                                        background: 'var(--bg-card)',
                                        borderRadius: 'var(--radius-sm)',
                                        border: '1px solid var(--border-subtle)',
                                    }}
                                >
                                    <span style={{ fontSize: 14, color: 'var(--text-primary)' }}>{a.title}</span>
                                    <span style={{ color: 'var(--success)', fontSize: 12 }}>✓ Verified</span>
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {isOtherUser && (
                <div style={{ marginTop: 16 }}>
                    <button
                        onClick={handleMessage}
                        disabled={!!msgStatus}
                        className={msgStatus ? 'btn-ghost' : 'btn-primary'}
                        style={msgStatus ? { opacity: 0.6, cursor: 'default' } : {}}
                    >
                        {msgStatus || 'Message'}
                    </button>
                </div>
            )}
        </div>
    );
}
