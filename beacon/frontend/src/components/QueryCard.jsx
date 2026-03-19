import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import ProvisionalAnswerBox from './ProvisionalAnswerBox';
import ConflictAlert from './ConflictAlert';
import { submitFollowUp, rateQuery, submitFollowThrough, finalizeQuery, getQueryStatus } from '../api/query';
import { useAuthStore } from '../store/authStore';

/**
 * QueryCard — dark glass card with status badge, answer sections, finalize button, and follow-up input.
 */
export default function QueryCard({ query: initialQuery }) {
    const userId = useAuthStore((s) => s.userId);
    const [query, setQuery] = useState(initialQuery);
    const [followUpText, setFollowUpText] = useState('');
    const [followUpResult, setFollowUpResult] = useState(null);
    const [followUpLoading, setFollowUpLoading] = useState(false);

    // Rating state
    const [hoverStar, setHoverStar] = useState(0);
    const [ratingLoading, setRatingLoading] = useState(false);
    const [ratingMsg, setRatingMsg] = useState('');

    // Follow-through state
    const [ftLoading, setFtLoading] = useState(false);
    const [ftMsg, setFtMsg] = useState('');
    const [showProofInput, setShowProofInput] = useState(false);
    const [proofUrl, setProofUrl] = useState('');

    // Finalize state
    const [finalizeLoading, setFinalizeLoading] = useState(false);
    const [finalizeError, setFinalizeError] = useState('');
    const [timeRemaining, setTimeRemaining] = useState(null);

    if (!query) return null;

    const isResolved = query.is_resolved || query.status === 'RESOLVED';
    const canFinalize = query.can_finalize || (
        !isResolved && (query.responses_received > 0 || query.faq_completed_count > 0)
    );

    // Countdown timer for response deadline
    useEffect(() => {
        if (isResolved || !query.response_deadline) return;
        const deadline = new Date(query.response_deadline);
        const tick = () => {
            const now = new Date();
            const diff = Math.max(0, Math.floor((deadline - now) / 1000));
            setTimeRemaining(diff);
        };
        tick();
        const interval = setInterval(tick, 1000);
        return () => clearInterval(interval);
    }, [query.response_deadline, isResolved]);

    // Poll for response status when query is pending/in-progress
    useEffect(() => {
        if (isResolved || !query.query_id || query._pending) return;
        const poll = async () => {
            try {
                const statusData = await getQueryStatus(query.query_id);
                setQuery((prev) => ({ ...prev, ...statusData }));
            } catch { /* ignore */ }
        };
        const interval = setInterval(poll, 15000);
        return () => clearInterval(interval);
    }, [query.query_id, isResolved, query._pending]);

    const formatTime = (seconds) => {
        if (seconds == null) return '';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}h ${m}m`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    };

    const handleFinalize = async () => {
        setFinalizeLoading(true);
        setFinalizeError('');
        try {
            const result = await finalizeQuery(query.query_id, { student_id: userId });
            setQuery((prev) => ({
                ...prev,
                ...result,
                is_resolved: true,
                status: 'RESOLVED',
            }));
        } catch (err) {
            setFinalizeError(err?.response?.data?.error || 'Failed to finalize.');
        } finally {
            setFinalizeLoading(false);
        }
    };

    const handleRate = async (rating) => {
        setRatingLoading(true);
        setRatingMsg('');
        try {
            await rateQuery(query.query_id, { student_id: userId, rating });
            setQuery((prev) => ({ ...prev, student_rating: rating }));
            setRatingMsg('Thanks for your feedback!');
        } catch {
            setRatingMsg('Failed to submit rating.');
        } finally {
            setRatingLoading(false);
        }
    };

    const handleFollowThrough = async (success) => {
        setFtLoading(true);
        setFtMsg('');
        try {
            await submitFollowThrough(query.query_id, {
                student_id: userId,
                success,
                proof_url: proofUrl.trim() || '',
            });
            setQuery((prev) => ({ ...prev, follow_through_success: success, follow_through_proof: proofUrl.trim() }));
            setFtMsg(success ? 'Glad it helped!' : 'Thanks for letting us know.');
            setShowProofInput(false);
        } catch {
            setFtMsg('Failed to submit.');
        } finally {
            setFtLoading(false);
        }
    };

    const handleFollowUp = async (e) => {
        e.preventDefault();
        if (!followUpText.trim()) return;
        setFollowUpLoading(true);
        setFollowUpResult(null);
        try {
            const result = await submitFollowUp(query.query_id, {
                student_id: userId,
                content: followUpText.trim(),
            });
            setFollowUpResult(result);
        } catch {
            setFollowUpResult({ source: 'ERROR', message: 'Failed to submit follow-up. Please try again.' });
        } finally {
            setFollowUpLoading(false);
        }
    };

    const handleSuggestionClick = (question) => {
        setFollowUpText(question);
    };

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

            {/* Response status & Finalize button — shown when query is pending/in-progress */}
            {!isResolved && (query.responses_received > 0 || query.faq_completed_count > 0) && (
                <div style={{
                    marginTop: 12,
                    padding: 14,
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-glass)',
                    border: '1px solid var(--border-subtle)',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                        <div>
                            <p style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
                                Senior Responses
                            </p>
                            <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)' }}>
                                {query.faq_completed_count || query.responses_received || 0} of {query.total_assigned || '?'} seniors responded
                            </p>
                            {timeRemaining != null && timeRemaining > 0 && (
                                <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--accent)' }}>
                                    ⏱ Time remaining: {formatTime(timeRemaining)}
                                </p>
                            )}
                            {timeRemaining === 0 && (
                                <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--warning)' }}>
                                    ⏰ Response window has expired
                                </p>
                            )}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {canFinalize && (
                                <button
                                    onClick={handleFinalize}
                                    disabled={finalizeLoading}
                                    className="btn-primary"
                                    style={{ padding: '8px 16px', fontSize: 13, whiteSpace: 'nowrap' }}
                                >
                                    {finalizeLoading ? 'Finalizing...' : '✅ Accept Answers Now'}
                                </button>
                            )}
                            {canFinalize && !finalizeLoading && (
                                <span style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
                                    or wait for more responses
                                </span>
                            )}
                        </div>
                    </div>
                    {finalizeError && (
                        <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--error)' }}>
                            ⚠ {finalizeError}
                        </p>
                    )}
                </div>
            )}

            {/* Waiting for responses message when no responses yet */}
            {!isResolved && query.total_assigned > 0 && (query.responses_received || 0) === 0 && (query.faq_completed_count || 0) === 0 && (
                <div style={{
                    marginTop: 12,
                    padding: 12,
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-glass)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'center',
                }}>
                    <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)' }}>
                        ⏳ Waiting for senior responses ({query.total_assigned} seniors assigned)
                        {timeRemaining != null && timeRemaining > 0 && (
                            <span> — {formatTime(timeRemaining)} remaining</span>
                        )}
                    </p>
                </div>
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
                            {query.finalized_by && (
                                <span style={{
                                    fontSize: 11, fontWeight: 400, marginLeft: 10,
                                    color: 'var(--text-muted)', fontStyle: 'italic',
                                }}>
                                    {query.finalized_by === 'STUDENT' ? '(early finalized by you)' :
                                     query.finalized_by === 'DEADLINE' ? '(auto-finalized at deadline)' :
                                     query.finalized_by === 'ALL_RESPONDED' ? '(all seniors responded)' : ''}
                                </span>
                            )}
                        </h4>
                        {query.majority_count != null && query.total_responses_considered != null && (
                            <p style={{ margin: '0 0 8px', fontSize: 12, color: 'var(--text-muted)' }}>
                                Based on majority of {query.majority_count}/{query.total_responses_considered} senior responses
                                {query.majority_label ? ` — "${query.majority_label}"` : ''}
                            </p>
                        )}
                        <div style={{ margin: 0, color: 'var(--text-primary)', lineHeight: 1.7, fontSize: 14 }}>
                            <ReactMarkdown>{query.final_answer}</ReactMarkdown>
                        </div>
                    </div>

                    <ConflictAlert
                        detected={query.conflict_detected}
                        details={query.conflict_details}
                    />

                    {/* Star Rating */}
                    <div style={{
                        marginTop: 14,
                        padding: 14,
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-glass)',
                        border: '1px solid var(--border-subtle)',
                    }}>
                        <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
                            Rate this advice
                        </p>
                        {query.student_rating ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <span key={star} style={{ fontSize: 22, color: star <= query.student_rating ? '#f59e0b' : '#444' }}>
                                        ★
                                    </span>
                                ))}
                                <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>Rated</span>
                            </div>
                        ) : (
                            <>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <span
                                            key={star}
                                            onClick={() => !ratingLoading && handleRate(star)}
                                            onMouseEnter={() => setHoverStar(star)}
                                            onMouseLeave={() => setHoverStar(0)}
                                            style={{
                                                fontSize: 24,
                                                cursor: ratingLoading ? 'default' : 'pointer',
                                                color: star <= hoverStar ? '#f59e0b' : '#555',
                                                transition: 'color 0.15s',
                                            }}
                                        >
                                            ★
                                        </span>
                                    ))}
                                    {ratingLoading && <span style={{ fontSize: 12, color: '#999', marginLeft: 8 }}>Saving...</span>}
                                </div>
                                {ratingMsg && <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--success)' }}>{ratingMsg}</p>}
                            </>
                        )}
                    </div>

                    {/* Follow-Through */}
                    <div style={{
                        marginTop: 10,
                        padding: 14,
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-glass)',
                        border: '1px solid var(--border-subtle)',
                    }}>
                        <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
                            Did this advice help you succeed?
                        </p>
                        {query.follow_through_success !== null && query.follow_through_success !== undefined ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontSize: 18 }}>{query.follow_through_success ? '👍' : '👎'}</span>
                                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                                    {query.follow_through_success ? 'Marked as helpful' : 'Marked as not helpful'}
                                </span>
                                {query.follow_through_proof && (
                                    <a href={query.follow_through_proof} target="_blank" rel="noopener noreferrer"
                                        style={{ fontSize: 12, color: 'var(--accent)', marginLeft: 8 }}>
                                        View proof
                                    </a>
                                )}
                            </div>
                        ) : (
                            <>
                                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                                    <button
                                        onClick={() => handleFollowThrough(true)}
                                        disabled={ftLoading}
                                        className="btn-success"
                                        style={{ padding: '6px 14px', fontSize: 13 }}
                                    >
                                        👍 Yes, it helped
                                    </button>
                                    <button
                                        onClick={() => handleFollowThrough(false)}
                                        disabled={ftLoading}
                                        className="btn-secondary"
                                        style={{ padding: '6px 14px', fontSize: 13 }}
                                    >
                                        👎 Not really
                                    </button>
                                    <button
                                        onClick={() => setShowProofInput(!showProofInput)}
                                        type="button"
                                        style={{
                                            background: 'none', border: 'none', color: 'var(--accent)',
                                            fontSize: 12, cursor: 'pointer', textDecoration: 'underline',
                                        }}
                                    >
                                        {showProofInput ? 'Hide proof' : 'Attach proof'}
                                    </button>
                                </div>
                                {showProofInput && (
                                    <input
                                        type="url"
                                        placeholder="Paste proof URL (optional)..."
                                        value={proofUrl}
                                        onChange={(e) => setProofUrl(e.target.value)}
                                        className="dark-input"
                                        style={{ marginTop: 8, padding: '6px 10px', fontSize: 12, width: '100%' }}
                                    />
                                )}
                                {ftMsg && <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--success)' }}>{ftMsg}</p>}
                            </>
                        )}
                    </div>

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

                    {/* Follow-up question input */}
                    <div style={{
                        marginTop: 16,
                        borderTop: '1px solid var(--border-subtle)',
                        paddingTop: 14,
                    }}>
                        <h4 style={{ margin: '0 0 8px', fontSize: 14, color: 'var(--text-secondary)', fontWeight: 600 }}>
                            💬 Ask a Follow-up
                        </h4>

                        {/* Clickable predicted follow-up suggestions */}
                        {query.follow_up_questions && query.follow_up_questions.length > 0 && (
                            <div style={{ marginBottom: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                {query.follow_up_questions.map((q, i) => (
                                    <button
                                        key={i}
                                        type="button"
                                        onClick={() => handleSuggestionClick(q)}
                                        style={{
                                            background: 'var(--bg-glass)',
                                            border: '1px solid var(--border-medium)',
                                            borderRadius: 'var(--radius-md)',
                                            padding: '5px 10px',
                                            fontSize: 12,
                                            color: 'var(--accent)',
                                            cursor: 'pointer',
                                            transition: 'background 0.15s',
                                        }}
                                        onMouseEnter={(e) => e.target.style.background = 'var(--bg-glass-strong)'}
                                        onMouseLeave={(e) => e.target.style.background = 'var(--bg-glass)'}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        )}

                        <form onSubmit={handleFollowUp} style={{ display: 'flex', gap: 8 }}>
                            <input
                                type="text"
                                placeholder="Type a follow-up question..."
                                value={followUpText}
                                onChange={(e) => setFollowUpText(e.target.value)}
                                className="dark-input"
                                style={{ flex: 1, padding: '8px 12px', fontSize: 13 }}
                            />
                            <button
                                type="submit"
                                disabled={followUpLoading || !followUpText.trim()}
                                className="btn-primary"
                                style={{ padding: '8px 16px', fontSize: 13, whiteSpace: 'nowrap' }}
                            >
                                {followUpLoading ? '...' : 'Ask'}
                            </button>
                        </form>

                        {/* Follow-up result */}
                        {followUpResult && (
                            <div style={{
                                marginTop: 10,
                                padding: 12,
                                borderRadius: 'var(--radius-md)',
                                background: followUpResult.source === 'INSTANT_SENIOR_MATCH'
                                    ? 'var(--success-dim)'
                                    : followUpResult.source === 'PROVISIONAL_RAG_MATCH'
                                        ? 'var(--warning-dim)'
                                        : followUpResult.source === 'ERROR'
                                            ? 'var(--error-dim)'
                                            : 'var(--bg-glass)',
                                border: `1px solid ${
                                    followUpResult.source === 'INSTANT_SENIOR_MATCH'
                                        ? 'rgba(34,197,94,0.2)'
                                        : followUpResult.source === 'PROVISIONAL_RAG_MATCH'
                                            ? 'rgba(245,158,11,0.2)'
                                            : followUpResult.source === 'ERROR'
                                                ? 'rgba(239,68,68,0.2)'
                                                : 'var(--border-subtle)'
                                }`,
                            }}>
                                {followUpResult.source === 'INSTANT_SENIOR_MATCH' && (
                                    <>
                                        <p style={{ margin: '0 0 4px', fontSize: 12, fontWeight: 600, color: 'var(--success)' }}>
                                            ⚡ Instant Answer (matched from senior FAQ)
                                        </p>
                                        <div style={{ margin: 0, fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                                            <ReactMarkdown>{followUpResult.answer}</ReactMarkdown>
                                        </div>
                                        {followUpResult.confidence && (
                                            <p style={{ margin: '6px 0 0', fontSize: 11, color: 'var(--text-muted)' }}>
                                                Confidence: {(followUpResult.confidence * 100).toFixed(0)}%
                                            </p>
                                        )}
                                    </>
                                )}
                                {followUpResult.source === 'PROVISIONAL_RAG_MATCH' && (
                                    <>
                                        <p style={{ margin: '0 0 4px', fontSize: 12, fontWeight: 600, color: 'var(--warning)' }}>
                                            🤖 Provisional Answer (from similar past questions)
                                        </p>
                                        <div style={{ margin: 0, fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                                            <ReactMarkdown>{followUpResult.answer}</ReactMarkdown>
                                        </div>
                                        {followUpResult.disclaimer && (
                                            <p style={{ margin: '6px 0 0', fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                                                {followUpResult.disclaimer}
                                            </p>
                                        )}
                                    </>
                                )}
                                {followUpResult.source === 'PENDING_SENIOR' && (
                                    <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)' }}>
                                        ⏳ {followUpResult.message}
                                    </p>
                                )}
                                {followUpResult.source === 'ERROR' && (
                                    <p style={{ margin: 0, fontSize: 13, color: 'var(--error)' }}>
                                        ❌ {followUpResult.message}
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
