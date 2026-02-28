import React from 'react';

/**
 * MessageRequestCard — shows a pending message request with accept/reject.
 * Props: { request, onAccept, onReject }
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
        <div
            style={{
                border: '1px solid #e5e7eb',
                borderRadius: 12,
                padding: 16,
                marginBottom: 10,
                background: '#fff',
                boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h4 style={{ margin: 0, fontSize: 15 }}>{request.student_name}</h4>
                    <p style={{ margin: '4px 0', color: '#6b7280', fontSize: 13 }}>
                        {timeSince(request.created_at)}
                    </p>
                </div>
                {!isPending && (
                    <span
                        style={{
                            padding: '2px 10px',
                            borderRadius: 9999,
                            fontSize: 12,
                            fontWeight: 600,
                            color: '#fff',
                            backgroundColor: request.status === 'ACCEPTED' ? '#22c55e' : '#ef4444',
                        }}
                    >
                        {request.status}
                    </span>
                )}
            </div>

            <p style={{ margin: '8px 0', fontSize: 14, color: '#374151' }}>
                {request.preview_text}
            </p>

            {isPending && (
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button
                        onClick={() => onAccept(request.id)}
                        style={{
                            padding: '6px 16px',
                            borderRadius: 8,
                            border: 'none',
                            background: '#22c55e',
                            color: '#fff',
                            cursor: 'pointer',
                            fontSize: 13,
                            fontWeight: 500,
                        }}
                    >
                        Accept
                    </button>
                    <button
                        onClick={() => onReject(request.id)}
                        style={{
                            padding: '6px 16px',
                            borderRadius: 8,
                            border: 'none',
                            background: '#ef4444',
                            color: '#fff',
                            cursor: 'pointer',
                            fontSize: 13,
                            fontWeight: 500,
                        }}
                    >
                        Reject
                    </button>
                </div>
            )}
        </div>
    );
}
