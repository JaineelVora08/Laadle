import React from 'react';

/**
 * MessageRequestCard — dark glass card for pending message requests.
 */
export default function MessageRequestCard({ request, onAccept, onReject }) {
    if (!request) return null;

    const timeSince = (dateStr) => {
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    };

    const isPending = request.status === 'PENDING';

    return (
        <div className="glass-card-static" style={{ padding: 16, marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h4 style={{ margin: 0, fontSize: 15, color: 'var(--text-primary)' }}>{request.student_name}</h4>
                    <p style={{ margin: '4px 0', color: 'var(--text-muted)', fontSize: 13 }}>
                        {timeSince(request.created_at)}
                        {request.domain_name ? ` • ${request.domain_name}` : ''}
                    </p>
                </div>
                {!isPending && (
                    <span className={`badge ${request.status === 'ACCEPTED' ? 'badge-resolved' : 'badge-pending'}`}>
                        {request.status}
                    </span>
                )}
            </div>

            <p style={{ margin: '8px 0', fontSize: 14, color: 'var(--text-secondary)' }}>
                {request.preview_text}
            </p>

            {isPending && (
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button onClick={() => onAccept(request.id)} className="btn-success" style={{ padding: '6px 16px', fontSize: 13 }}>
                        Accept
                    </button>
                    <button onClick={() => onReject(request.id)} className="btn-danger" style={{ padding: '6px 16px', fontSize: 13 }}>
                        Reject
                    </button>
                </div>
            )}
        </div>
    );
}
