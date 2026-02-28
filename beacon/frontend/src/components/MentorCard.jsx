import React from 'react';
import { useNavigate } from 'react-router-dom';
import { connectMentor } from '../api/mentorMatching';
import { useAuthStore } from '../store/authStore';
import TrustScoreBadge from './TrustScoreBadge';

/**
 * MentorCard — shows a matched senior's info with connect/view buttons.
 * Props: { mentor, domainId }
 */
export default function MentorCard({ mentor, domainId }) {
    const navigate = useNavigate();
    const userId = useAuthStore((s) => s.userId);
    const [status, setStatus] = React.useState(null);

    const handleConnect = async () => {
        try {
            await connectMentor({
                student_id: userId,
                senior_id: mentor.senior_id,
                domain_id: domainId,
            });
            setStatus('Request Sent ✓');
        } catch {
            setStatus('Failed to connect');
        }
    };

    return (
        <div
            style={{
                border: '1px solid #e5e7eb',
                borderRadius: 12,
                padding: 20,
                marginBottom: 12,
                background: '#fff',
                boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: 18 }}>{mentor.name}</h3>
                    <p style={{ margin: '4px 0', color: '#6b7280', fontSize: 14 }}>
                        {mentor.experience_level} • {mentor.years_of_involvement} year{mentor.years_of_involvement !== 1 ? 's' : ''} involvement
                    </p>
                    <p style={{ margin: '4px 0', fontSize: 14 }}>
                        <span
                            style={{
                                display: 'inline-block',
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                backgroundColor: mentor.availability ? '#22c55e' : '#ef4444',
                                marginRight: 6,
                            }}
                        />
                        {mentor.availability ? 'Available' : 'Unavailable'}
                    </p>
                </div>
                <TrustScoreBadge score={mentor.trust_score} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                    onClick={() => navigate(`/profile/${mentor.senior_id}`)}
                    style={{
                        padding: '6px 16px',
                        borderRadius: 8,
                        border: '1px solid #d1d5db',
                        background: '#fff',
                        cursor: 'pointer',
                        fontSize: 13,
                    }}
                >
                    View Profile
                </button>
                <button
                    onClick={handleConnect}
                    disabled={!!status}
                    style={{
                        padding: '6px 16px',
                        borderRadius: 8,
                        border: 'none',
                        background: status ? '#d1d5db' : '#3b82f6',
                        color: status ? '#6b7280' : '#fff',
                        cursor: status ? 'default' : 'pointer',
                        fontSize: 13,
                    }}
                >
                    {status || 'Connect'}
                </button>
            </div>
        </div>
    );
}
