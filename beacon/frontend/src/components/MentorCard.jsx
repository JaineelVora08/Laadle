import React from 'react';
import { useNavigate } from 'react-router-dom';
import { connectMentor } from '../api/mentorMatching';
import { useAuthStore } from '../store/authStore';
import TrustScoreBadge from './TrustScoreBadge';

/**
 * MentorCard — dark glass card with mentor info and connect button.
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
        <div className="glass-card" style={{ padding: 20, marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: 18, color: 'var(--text-heading)' }}>{mentor.name}</h3>
                    <p style={{ margin: '4px 0', color: 'var(--text-secondary)', fontSize: 14 }}>
                        {mentor.experience_level} • {mentor.years_of_involvement} year{mentor.years_of_involvement !== 1 ? 's' : ''} involvement
                    </p>
                    <p style={{ margin: '4px 0', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className={`status-dot ${mentor.availability ? 'online' : 'offline'}`} />
                        <span style={{ color: 'var(--text-secondary)' }}>
                            {mentor.availability ? 'Available' : 'Unavailable'}
                        </span>
                    </p>
                </div>
                <TrustScoreBadge score={mentor.trust_score} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                    onClick={() => navigate(`/profile/${mentor.senior_id}`)}
                    className="btn-ghost"
                >
                    View Profile
                </button>
                <button
                    onClick={handleConnect}
                    disabled={!!status}
                    className={status ? 'btn-ghost' : 'btn-primary'}
                    style={status ? { opacity: 0.6, cursor: 'default' } : {}}
                >
                    {status || 'Connect'}
                </button>
            </div>
        </div>
    );
}
