import React from 'react';
import ReactMarkdown from 'react-markdown';
import ProvisionalAnswerBox from './ProvisionalAnswerBox';
import ConflictAlert from './ConflictAlert';

/**
 * QueryCard — shows a query with provisional/final answer, status badge, and conflict alert.
 * Props: { query }
 */
export default function QueryCard({ query }) {
    if (!query) return null;

    const isResolved = query.is_resolved || query.status === 'RESOLVED';

    return (
        <div
            style={{
                border: '1px solid #e5e7eb',
                borderRadius: 12,
                padding: 20,
                marginBottom: 16,
                background: '#fff',
                boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}
        >
            {query.content && (
                <p style={{ margin: '0 0 8px', fontWeight: 500 }}>{query.content}</p>
            )}

            <span
                style={{
                    display: 'inline-block',
                    padding: '2px 10px',
                    borderRadius: 9999,
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#fff',
                    backgroundColor: isResolved ? '#22c55e' : '#f59e0b',
                    marginBottom: 12,
                }}
            >
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
                            background: '#f0fdf4',
                            border: '1px solid #22c55e',
                            borderRadius: 12,
                            padding: 16,
                            marginTop: 8,
                        }}
                    >
                        <h4 style={{ margin: '0 0 6px', color: '#166534', fontSize: 15 }}>
                            ✅ Final Answer
                        </h4>
                        <div style={{ margin: 0, color: '#1f2937', lineHeight: 1.7, fontSize: 14 }}>
                            <ReactMarkdown>{query.final_answer}</ReactMarkdown>
                        </div>
                    </div>

                    <ConflictAlert
                        detected={query.conflict_detected}
                        details={query.conflict_details}
                    />

                    {query.contributing_seniors && query.contributing_seniors.length > 0 && (
                        <div style={{ marginTop: 12 }}>
                            <p style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 600, color: '#6b7280' }}>
                                Contributing seniors:
                            </p>
                            {query.contributing_seniors.map((s, i) => (
                                <span
                                    key={i}
                                    style={{
                                        display: 'inline-block',
                                        padding: '2px 10px',
                                        borderRadius: 9999,
                                        fontSize: 12,
                                        background: '#e0e7ff',
                                        color: '#3730a3',
                                        marginRight: 6,
                                    }}
                                >
                                    {s.senior_id?.slice(0, 8)}… (weight: {(s.weight * 100).toFixed(0)}%)
                                </span>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
