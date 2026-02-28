import React from 'react';
import { sendMessageRequest } from '../api/messaging';
import { useAuthStore } from '../store/authStore';
import TrustScoreBadge from './TrustScoreBadge';

/**
 * ProfileCard — renders user profile info with trust score, achievements, and message button.
 * Props: { user: UserProfileResponse }
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
        <div
            style={{
                border: '1px solid #e5e7eb',
                borderRadius: 12,
                padding: 24,
                background: '#fff',
                boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
                marginBottom: 16,
            }}
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h2 style={{ margin: 0 }}>{user.name}</h2>
                    <span
                        style={{
                            display: 'inline-block',
                            padding: '2px 10px',
                            borderRadius: 9999,
                            fontSize: 12,
                            fontWeight: 600,
                            color: '#fff',
                            backgroundColor: user.role === 'SENIOR' ? '#8b5cf6' : '#3b82f6',
                            marginTop: 4,
                        }}
                    >
                        {user.role}
                    </span>
                    {user.current_level && (
                        <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: 14 }}>{user.current_level}</p>
                    )}
                </div>
                <TrustScoreBadge score={user.trust_score} />
            </div>

            <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                    style={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        backgroundColor: user.availability ? '#22c55e' : '#ef4444',
                        display: 'inline-block',
                    }}
                />
                <span style={{ fontSize: 14, color: '#374151' }}>
                    {user.availability ? 'Available' : 'Unavailable'}
                </span>
            </div>

            {user.achievements && user.achievements.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <h4 style={{ margin: '0 0 8px' }}>Achievements</h4>
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                        {user.achievements
                            .filter((a) => a.verified)
                            .map((a) => (
                                <li key={a.id} style={{ fontSize: 14, marginBottom: 4 }}>
                                    {a.title}{' '}
                                    <span style={{ color: '#22c55e', fontSize: 12 }}>✓ Verified</span>
                                </li>
                            ))}
                    </ul>
                </div>
            )}

            {isOtherUser && (
                <div style={{ marginTop: 16 }}>
                    <button
                        onClick={handleMessage}
                        disabled={!!msgStatus}
                        style={{
                            padding: '8px 20px',
                            borderRadius: 8,
                            border: 'none',
                            background: msgStatus ? '#d1d5db' : '#3b82f6',
                            color: msgStatus ? '#6b7280' : '#fff',
                            cursor: msgStatus ? 'default' : 'pointer',
                            fontSize: 14,
                        }}
                    >
                        {msgStatus || 'Message'}
                    </button>
                </div>
            )}
        </div>
    );
}
