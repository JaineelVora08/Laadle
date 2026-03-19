import React from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * ProvisionalAnswerBox — dark theme AI answer card.
 */
export default function ProvisionalAnswerBox({ answer, disclaimer, followups }) {
    if (answer === null || answer === undefined) {
        return (
            <div
                style={{
                    background: 'var(--warning-dim)',
                    border: '1px solid rgba(245,158,11,0.2)',
                    borderRadius: 'var(--radius-md)',
                    padding: 20,
                    marginTop: 12,
                    textAlign: 'center',
                }}
            >
                <div
                    style={{
                        width: 24,
                        height: 24,
                        border: '3px solid var(--warning)',
                        borderTop: '3px solid transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        margin: '0 auto 8px',
                    }}
                />
                <p style={{ margin: 0, color: 'var(--warning)', fontWeight: 500 }}>
                    Generating AI provisional answer...
                </p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    return (
        <div
            style={{
                background: 'var(--warning-dim)',
                border: '1px solid rgba(245,158,11,0.2)',
                borderRadius: 'var(--radius-md)',
                padding: 20,
                marginTop: 12,
            }}
        >
            <h4 style={{ margin: '0 0 8px', color: 'var(--warning)', fontSize: 15 }}>
                🤖 AI First-Look Answer
            </h4>
            <div style={{ margin: '0 0 8px', color: 'var(--text-primary)', lineHeight: 1.7, fontSize: 14 }}>
                <ReactMarkdown>{answer}</ReactMarkdown>
            </div>
            {disclaimer && (
                <p style={{ margin: '0 0 12px', color: 'var(--text-muted)', fontSize: 12, fontStyle: 'italic' }}>
                    {disclaimer}
                </p>
            )}
            {followups && followups.length > 0 && (
                <div style={{ borderTop: '1px solid rgba(245,158,11,0.15)', paddingTop: 12 }}>
                    <p style={{ margin: '0 0 6px', fontWeight: 600, fontSize: 13, color: 'var(--warning)' }}>
                        You might also want to ask:
                    </p>
                    <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {followups.map((q, i) => (
                            <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>
                                {q}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
