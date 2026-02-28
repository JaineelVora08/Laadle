import React from 'react';
import ReactMarkdown from 'react-markdown';
import ProvisionalAnswerBox from './ProvisionalAnswerBox';
import ConflictAlert from './ConflictAlert';

/**
 * QueryCard — dark glass card with status badge and answer sections.
 */
export default function QueryCard({ query }) {
    if (!query) return null;

    const isResolved = query.is_resolved || query.status === 'RESOLVED';

    return (
        <div className="glass-card-static" style={{ padding: 20, marginBottom: 16 }}>
            {query.content && (
                <p style={{ margin: '0 0 8px', fontWeight: 500, color: 'var(--text-primary)' }}>{query.content}</p>
            )}

            <span className={`badge ${isResolved ? 'badge-resolved' : 'badge-pending'}`} style={{ marginBottom: 12 }}>
                {isResolved ? 'RESOLVED' : query.status || 'PENDING_SENIOR'}
            </span>

            {!isResolved && (
                <ProvisionalAnswerBox
                    answer={query.provisional_answer}
                    disclaimer={query.disclaimer}
                    followups={query.predicted_followups}
                />
            )}

            {isResolved && (
                <>
                    <div
                        style={{
                            background: 'var(--success-dim)',
                            border: '1px solid rgba(34,197,94,0.2)',
                            borderRadius: 'var(--radius-md)',
                            padding: 16,
                            marginTop: 8,
                        }}
                    >
                        <h4 style={{ margin: '0 0 6px', color: 'var(--success)', fontSize: 15 }}>
                            ✅ Final Answer
                        </h4>
                        <div style={{ margin: 0, color: 'var(--text-primary)', lineHeight: 1.7, fontSize: 14 }}>
                            <ReactMarkdown>{query.final_answer}</ReactMarkdown>
                        </div>
                    </div>

                    <ConflictAlert
                        detected={query.conflict_detected}
                        details={query.conflict_details}
                    />

                    {query.contributing_seniors && query.contributing_seniors.length > 0 && (
                        <div style={{ marginTop: 12 }}>
                            <p style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
                                Contributing seniors:
                            </p>
                            {query.contributing_seniors.map((s, i) => (
                                <span
                                    key={i}
                                    className="badge badge-role"
                                    style={{ marginRight: 6 }}
                                >
                                    {s.senior_id?.slice(0, 8)}… ({(s.weight * 100).toFixed(0)}%)
                                </span>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
