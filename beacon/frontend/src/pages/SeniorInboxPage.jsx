import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { getSeniorPendingQueries, submitSeniorResponse } from '../api/query';
import ProvisionalAnswerBox from '../components/ProvisionalAnswerBox';

/**
 * SeniorInboxPage — view pending queries and submit responses.
 */
export default function SeniorInboxPage() {
    const userId = useAuthStore((s) => s.userId);

    const [pendingQueries, setPendingQueries] = useState([]);
    const [selectedQuery, setSelectedQuery] = useState(null);
    const [adviceContent, setAdviceContent] = useState('');
    const [answeredFollowups, setAnsweredFollowups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    useEffect(() => {
        if (!userId) return;
        setLoading(true);
        getSeniorPendingQueries(userId)
            .then((data) => setPendingQueries(Array.isArray(data) ? data : []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [userId]);

    const handleSelectQuery = (query) => {
        setSelectedQuery(query);
        setAdviceContent('');
        setSuccessMsg('');
        // Initialize follow-up answer slots
        const followups = query.predicted_followups || [];
        setAnsweredFollowups(followups.map((q) => ({ question: q, answer: '' })));
    };

    const handleFollowupAnswer = (index, answer) => {
        setAnsweredFollowups((prev) =>
            prev.map((item, i) => (i === index ? { ...item, answer } : item))
        );
    };

    const handleSubmitResponse = async (e) => {
        e.preventDefault();
        if (!selectedQuery || !adviceContent.trim()) return;

        setSubmitting(true);
        try {
            await submitSeniorResponse(selectedQuery.query_id, {
                senior_id: userId,
                advice_content: adviceContent.trim(),
                answered_followups: answeredFollowups.filter((f) => f.answer.trim()),
            });
            // Remove from pending list
            setPendingQueries((prev) => prev.filter((q) => q.query_id !== selectedQuery.query_id));
            setSelectedQuery(null);
            setAdviceContent('');
            setAnsweredFollowups([]);
            setSuccessMsg('Response submitted successfully! ✓');
        } catch {
            setSuccessMsg('Failed to submit response.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div style={{ maxWidth: 1100, margin: '2rem auto', padding: '0 16px' }}>
            <h2>Senior Inbox 📥</h2>

            {successMsg && (
                <p style={{ color: '#22c55e', fontWeight: 500, marginBottom: 12 }}>{successMsg}</p>
            )}

            <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
                {/* Left panel — query list */}
                <div style={{ flex: '0 0 320px' }}>
                    <h3 style={{ marginTop: 0 }}>Pending Queries ({pendingQueries.length})</h3>
                    {loading ? (
                        <p style={{ color: '#9ca3af' }}>Loading...</p>
                    ) : pendingQueries.length === 0 ? (
                        <p style={{ color: '#9ca3af' }}>No pending queries. Check back later!</p>
                    ) : (
                        pendingQueries.map((q) => (
                            <div
                                key={q.query_id}
                                onClick={() => handleSelectQuery(q)}
                                style={{
                                    border: `1px solid ${selectedQuery?.query_id === q.query_id ? '#3b82f6' : '#e5e7eb'}`,
                                    borderRadius: 10,
                                    padding: 14,
                                    marginBottom: 8,
                                    cursor: 'pointer',
                                    background: selectedQuery?.query_id === q.query_id ? '#eff6ff' : '#fff',
                                    transition: 'border-color 0.15s',
                                }}
                            >
                                <p style={{ margin: 0, fontWeight: 500, fontSize: 14 }}>
                                    {(q.content || '').slice(0, 80)}{q.content?.length > 80 ? '…' : ''}
                                </p>
                                <p style={{ margin: '4px 0 0', color: '#9ca3af', fontSize: 12 }}>
                                    {q.domain_id?.slice(0, 8)}… • {q.timestamp ? new Date(q.timestamp).toLocaleDateString() : 'Recent'}
                                </p>
                            </div>
                        ))
                    )}
                </div>

                {/* Right panel — response form */}
                <div style={{ flex: 1 }}>
                    {selectedQuery ? (
                        <>
                            <h3 style={{ marginTop: 0 }}>Query Detail</h3>
                            <div
                                style={{
                                    background: '#f9fafb',
                                    borderRadius: 12,
                                    padding: 16,
                                    marginBottom: 16,
                                    border: '1px solid #e5e7eb',
                                }}
                            >
                                <p style={{ margin: 0, lineHeight: 1.6 }}>{selectedQuery.content}</p>
                            </div>

                            <ProvisionalAnswerBox
                                answer={selectedQuery.provisional_answer}
                                disclaimer="This is what the AI told the student. Please provide your expert input."
                                followups={selectedQuery.predicted_followups}
                            />

                            {/* Follow-up answers */}
                            {answeredFollowups.length > 0 && (
                                <div style={{ marginTop: 20 }}>
                                    <h4>Predicted Follow-up Questions</h4>
                                    {answeredFollowups.map((f, i) => (
                                        <div key={i} style={{ marginBottom: 12 }}>
                                            <p style={{ margin: '0 0 4px', fontWeight: 500, fontSize: 14 }}>
                                                {f.question}
                                            </p>
                                            <input
                                                type="text"
                                                placeholder="Your answer (optional)"
                                                value={f.answer}
                                                onChange={(e) => handleFollowupAnswer(i, e.target.value)}
                                                style={{
                                                    width: '100%',
                                                    padding: '8px 12px',
                                                    borderRadius: 8,
                                                    border: '1px solid #d1d5db',
                                                    fontSize: 14,
                                                    boxSizing: 'border-box',
                                                }}
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Main advice */}
                            <form onSubmit={handleSubmitResponse} style={{ marginTop: 20 }}>
                                <h4>Your Advice</h4>
                                <textarea
                                    placeholder="Write your expert advice here..."
                                    value={adviceContent}
                                    onChange={(e) => setAdviceContent(e.target.value)}
                                    rows={6}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        borderRadius: 10,
                                        border: '1px solid #d1d5db',
                                        fontSize: 14,
                                        resize: 'vertical',
                                        fontFamily: 'inherit',
                                        boxSizing: 'border-box',
                                    }}
                                />
                                <button
                                    type="submit"
                                    disabled={submitting || !adviceContent.trim()}
                                    style={{
                                        marginTop: 8,
                                        padding: '10px 24px',
                                        borderRadius: 8,
                                        border: 'none',
                                        background: submitting || !adviceContent.trim() ? '#d1d5db' : '#22c55e',
                                        color: '#fff',
                                        cursor: submitting || !adviceContent.trim() ? 'default' : 'pointer',
                                        fontSize: 14,
                                        fontWeight: 600,
                                    }}
                                >
                                    {submitting ? 'Submitting...' : 'Submit Response'}
                                </button>
                            </form>
                        </>
                    ) : (
                        <div style={{ textAlign: 'center', paddingTop: 60, color: '#9ca3af' }}>
                            <p style={{ fontSize: 18 }}>Select a query from the left panel to respond.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
