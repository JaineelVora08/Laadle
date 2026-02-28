import React from 'react';

/**
 * ProvisionalAnswerBox — AI first-look answer with disclaimer and follow-up questions.
 * Props: { answer, disclaimer, followups }
 */
export default function ProvisionalAnswerBox({ answer, disclaimer, followups }) {
    if (answer === null || answer === undefined) {
        return (
            <div
                style={{
                    background: '#fef3c7',
                    border: '1px solid #f59e0b',
                    borderRadius: 12,
                    padding: 20,
                    marginTop: 12,
                    textAlign: 'center',
                }}
            >
                <div
                    style={{
                        width: 24,
                        height: 24,
                        border: '3px solid #f59e0b',
                        borderTop: '3px solid transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        margin: '0 auto 8px',
                    }}
                />
                <p style={{ margin: 0, color: '#92400e', fontWeight: 500 }}>
                    Generating AI provisional answer...
                </p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    return (
        <div
            style={{
                background: '#fef3c7',
                border: '1px solid #f59e0b',
                borderRadius: 12,
                padding: 20,
                marginTop: 12,
            }}
        >
            <h4 style={{ margin: '0 0 8px', color: '#92400e', fontSize: 15 }}>
                🤖 AI First-Look Answer
            </h4>
            <p style={{ margin: '0 0 8px', color: '#1f2937', lineHeight: 1.6 }}>{answer}</p>
            {disclaimer && (
                <p style={{ margin: '0 0 12px', color: '#92400e', fontSize: 12, fontStyle: 'italic' }}>
                    {disclaimer}
                </p>
            )}
            {followups && followups.length > 0 && (
                <div style={{ borderTop: '1px solid #fbbf24', paddingTop: 12 }}>
                    <p style={{ margin: '0 0 6px', fontWeight: 600, fontSize: 13, color: '#92400e' }}>
                        You might also want to ask:
                    </p>
                    <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {followups.map((q, i) => (
                            <li key={i} style={{ fontSize: 13, color: '#78350f', marginBottom: 4 }}>
                                {q}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
