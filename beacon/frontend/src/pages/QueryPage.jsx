import React, { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { getUserDomains } from '../api/domains';
import { submitQuery, getQueryStatus, getStudentQueries } from '../api/query';
import DomainBadge from '../components/DomainBadge';
import QueryCard from '../components/QueryCard';
import EffectsLayout from '../components/EffectsLayout';

export default function QueryPage() {
    const userId = useAuthStore((s) => s.userId);

    const [content, setContent] = useState('');
    const [selectedDomains, setSelectedDomains] = useState([]);
    const [userDomains, setUserDomains] = useState([]);
    const [loading, setLoading] = useState(false);
    const [polling, setPolling] = useState(false);
    const [pollingQueryId, setPollingQueryId] = useState(null);
    const [timeoutMsg, setTimeoutMsg] = useState('');
    const [queries, setQueries] = useState([]);
    const intervalRef = useRef(null);
    const startTimeRef = useRef(null);

    // Load domains
    useEffect(() => {
        if (!userId) return;
        getUserDomains(userId)
            .then((data) => setUserDomains(Array.isArray(data) ? data : []))
            .catch(() => { });
    }, [userId]);

    // Load student queries from backend (persisted)
    useEffect(() => {
        if (!userId) return;
        getStudentQueries(userId)
            .then((data) => setQueries(Array.isArray(data) ? data : []))
            .catch(() => { });
    }, [userId]);

    // Cleanup interval
    useEffect(() => {
        return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
    }, []);

    const startPolling = (queryId) => {
        setPolling(true);
        setPollingQueryId(queryId);
        setTimeoutMsg('');
        startTimeRef.current = Date.now();
        intervalRef.current = setInterval(async () => {
            try {
                const statusData = await getQueryStatus(queryId);
                if (statusData.status === 'RESOLVED' || statusData.final_answer) {
                    clearInterval(intervalRef.current);
                    intervalRef.current = null;
                    // Update the query in our list
                    setQueries((prev) =>
                        prev.map((q) =>
                            q.query_id === queryId
                                ? { ...q, ...statusData, is_resolved: true }
                                : q
                        )
                    );
                    setPolling(false);
                    setPollingQueryId(null);
                }
            } catch { /* keep polling */ }
            if (Date.now() - startTimeRef.current > 5 * 60 * 1000) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
                setPolling(false);
                setPollingQueryId(null);
                setTimeoutMsg('Still waiting for senior response. We\'ll notify you.');
            }
        }, 10000);
    };

    const toggleDomain = (domain) => {
        setSelectedDomains((prev) => {
            const isSelected = prev.some((d) => d.domain_id === domain.domain_id);
            if (isSelected) {
                return prev.filter((d) => d.domain_id !== domain.domain_id);
            }
            return [...prev, domain];
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!content.trim() || selectedDomains.length === 0 || !userId) return;

        const questionText = content.trim();
        const tempId = `temp-${Date.now()}`;

        // Optimistic: add a pending query card immediately
        const optimisticQuery = {
            query_id: tempId,
            content: questionText,
            status: 'SUBMITTING',
            provisional_answer: null,  // triggers the spinner in ProvisionalAnswerBox
            _pending: true,
        };
        setQueries((prev) => [optimisticQuery, ...prev]);
        setContent('');
        setSelectedDomains([]);
        setLoading(true);

        try {
            const response = await submitQuery({
                student_id: userId,
                domain_ids: selectedDomains.map((d) => d.domain_id),
                content: questionText,
            });
            const newQuery = { ...response, content: questionText };
            // Replace optimistic card with real one
            setQueries((prev) =>
                prev.map((q) => q.query_id === tempId ? newQuery : q)
            );
            startPolling(response.query_id);
        } catch {
            // Mark the optimistic card as failed
            setQueries((prev) =>
                prev.map((q) =>
                    q.query_id === tempId
                        ? { ...q, status: 'FAILED', _pending: false, _failed: true }
                        : q
                )
            );
        } finally { setLoading(false); }
    };

    return (
        <EffectsLayout
            title="Ask a Question ❓"
            tagline="Select one or more domains, type your question, and get an AI provisional answer while a senior reviews it."
        >
            {/* Domain selector */}
            <div className="fx-glass fx-reveal">
                <h3 className="fx-section-title">Select domains</h3>
                {userDomains.length === 0 ? (
                    <p style={{ color: '#666', fontSize: 14 }}>Add domains from your dashboard to ask questions.</p>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {userDomains.map((d) => (
                            <DomainBadge
                                key={d.domain_id}
                                domain={d}
                                selected={selectedDomains.some((s) => s.domain_id === d.domain_id)}
                                onClick={() => toggleDomain(d)}
                            />
                        ))}
                    </div>
                )}
                {selectedDomains.length > 0 && (
                    <p style={{ fontSize: 13, color: '#999', marginTop: 8 }}>
                        Selected ({selectedDomains.length}):{' '}
                        <strong style={{ color: '#00b4d8' }}>
                            {selectedDomains.map((d) => d.name || d.domain_name).join(', ')}
                        </strong>
                    </p>
                )}
            </div>

            {/* Query form */}
            <div className="fx-glass fx-reveal">
                <form onSubmit={handleSubmit}>
                    <textarea
                        placeholder="Type your question here..."
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        rows={5}
                        className="dark-input"
                        style={{ marginBottom: 12 }}
                    />
                    <button type="submit" disabled={loading || !content.trim() || selectedDomains.length === 0} className="btn-primary">
                        {loading ? 'Submitting...' : 'Submit Question'}
                    </button>
                </form>
            </div>

            {/* Polling status */}
            {polling && (
                <div className="fx-glass" style={{ textAlign: 'center' }}>
                    <p style={{ color: '#999', fontSize: 13, margin: 0 }}>⏳ Waiting for senior response... (polling every 10s)</p>
                </div>
            )}
            {timeoutMsg && <p className="msg-error" style={{ marginBottom: 16 }}>{timeoutMsg}</p>}

            {/* All queries — always visible */}
            <div className="fx-reveal">
                <h3 className="fx-section-title">Your Queries ({queries.length})</h3>
                {queries.length === 0 ? (
                    <p style={{ color: '#666', fontSize: 14 }}>No queries yet. Ask your first question above!</p>
                ) : (
                    queries.map((q) => (
                        <div key={q.query_id}>
                            {q._failed ? (
                                <div className="glass-card-static" style={{ padding: 20, marginBottom: 16 }}>
                                    <p style={{ margin: '0 0 8px', fontWeight: 500, color: 'var(--text-primary)' }}>{q.content}</p>
                                    <div style={{
                                        background: 'var(--error-dim)',
                                        border: '1px solid rgba(239,68,68,0.2)',
                                        borderRadius: 'var(--radius-md)',
                                        padding: 14,
                                        textAlign: 'center',
                                    }}>
                                        <p style={{ margin: 0, color: 'var(--error)', fontWeight: 500 }}>
                                            ⚠ Failed to submit. Please try again.
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <QueryCard query={q} />
                            )}
                        </div>
                    ))
                )}
            </div>
        </EffectsLayout>
    );
}
