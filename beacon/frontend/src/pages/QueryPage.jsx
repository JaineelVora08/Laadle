import React, { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { useQueryStore } from '../store/queryStore';
import { getUserDomains } from '../api/domains';
import { submitQuery, getQueryStatus } from '../api/query';
import DomainBadge from '../components/DomainBadge';
import QueryCard from '../components/QueryCard';

/**
 * QueryPage — submit queries, see provisional answer, poll for final response.
 */
export default function QueryPage() {
    const userId = useAuthStore((s) => s.userId);
    const activeQuery = useQueryStore((s) => s.activeQuery);
    const addQuery = useQueryStore((s) => s.addQuery);
    const resolveQuery = useQueryStore((s) => s.resolveQuery);
    const setActiveQuery = useQueryStore((s) => s.setActiveQuery);

    const [content, setContent] = useState('');
    const [selectedDomain, setSelectedDomain] = useState(null);
    const [userDomains, setUserDomains] = useState([]);
    const [loading, setLoading] = useState(false);
    const [polling, setPolling] = useState(false);
    const [timeoutMsg, setTimeoutMsg] = useState('');
    const intervalRef = useRef(null);
    const startTimeRef = useRef(null);

    useEffect(() => {
        if (!userId) return;
        getUserDomains(userId)
            .then((data) => setUserDomains(Array.isArray(data) ? data : []))
            .catch(() => { });
    }, [userId]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, []);

    const startPolling = (queryId) => {
        setPolling(true);
        setTimeoutMsg('');
        startTimeRef.current = Date.now();

        intervalRef.current = setInterval(async () => {
            try {
                const statusData = await getQueryStatus(queryId);
                if (statusData.status === 'RESOLVED' || statusData.final_answer) {
                    clearInterval(intervalRef.current);
                    intervalRef.current = null;
                    resolveQuery(queryId, statusData);
                    setPolling(false);
                }
            } catch {
                // keep polling
            }

            // 5 minute timeout
            if (Date.now() - startTimeRef.current > 5 * 60 * 1000) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
                setPolling(false);
                setTimeoutMsg('Still waiting for senior response. We\'ll notify you.');
            }
        }, 10000);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!content.trim() || !selectedDomain || !userId) return;

        setLoading(true);
        try {
            const response = await submitQuery({
                student_id: userId,
                domain_id: selectedDomain.domain_id,
                content: content.trim(),
            });
            const queryWithContent = { ...response, content: content.trim() };
            addQuery(queryWithContent);
            setContent('');
            startPolling(response.query_id);
        } catch {
            // silently fail
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 800, margin: '2rem auto', padding: '0 16px' }}>
            <h2>Ask a Question ❓</h2>
            <p style={{ color: '#6b7280' }}>
                Select a domain, type your question, and get an AI provisional answer while a senior reviews it.
            </p>

            {/* Domain selector */}
            <div style={{ marginBottom: 16 }}>
                <p style={{ fontWeight: 600, marginBottom: 8 }}>Select domain:</p>
                {userDomains.length === 0 ? (
                    <p style={{ color: '#9ca3af', fontSize: 14 }}>
                        Add domains from your dashboard to ask questions.
                    </p>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {userDomains.map((d) => (
                            <DomainBadge
                                key={d.domain_id}
                                domain={d}
                                onClick={() => setSelectedDomain(d)}
                            />
                        ))}
                    </div>
                )}
                {selectedDomain && (
                    <p style={{ fontSize: 13, color: '#6b7280', marginTop: 6 }}>
                        Selected: <strong>{selectedDomain.name || selectedDomain.domain_name}</strong>
                    </p>
                )}
            </div>

            {/* Query form */}
            <form onSubmit={handleSubmit}>
                <textarea
                    placeholder="Type your question here..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={5}
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
                    disabled={loading || !content.trim() || !selectedDomain}
                    style={{
                        marginTop: 8,
                        padding: '10px 24px',
                        borderRadius: 8,
                        border: 'none',
                        background:
                            loading || !content.trim() || !selectedDomain ? '#d1d5db' : '#3b82f6',
                        color: '#fff',
                        cursor:
                            loading || !content.trim() || !selectedDomain ? 'default' : 'pointer',
                        fontSize: 14,
                        fontWeight: 600,
                    }}
                >
                    {loading ? 'Submitting...' : 'Submit Question'}
                </button>
            </form>

            {/* Polling indicator */}
            {polling && (
                <p style={{ marginTop: 12, color: '#6b7280', fontSize: 13 }}>
                    ⏳ Waiting for senior response... (polling every 10s)
                </p>
            )}
            {timeoutMsg && (
                <p style={{ marginTop: 12, color: '#f59e0b', fontSize: 13 }}>{timeoutMsg}</p>
            )}

            {/* Active query */}
            {activeQuery && (
                <div style={{ marginTop: 24 }}>
                    <h3>Your Query</h3>
                    <QueryCard query={activeQuery} />
                </div>
            )}
        </div>
    );
}
