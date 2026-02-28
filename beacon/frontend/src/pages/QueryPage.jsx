import React, { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { useQueryStore } from '../store/queryStore';
import { getUserDomains } from '../api/domains';
import { submitQuery, getQueryStatus } from '../api/query';
import DomainBadge from '../components/DomainBadge';
import QueryCard from '../components/QueryCard';
import EffectsLayout from '../components/EffectsLayout';

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

    useEffect(() => {
        return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
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
            } catch { /* keep polling */ }
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
            addQuery({ ...response, content: content.trim() });
            setContent('');
            startPolling(response.query_id);
        } catch { /* silently fail */ } finally { setLoading(false); }
    };

    return (
        <EffectsLayout
            title="Ask a Question ❓"
            tagline="Select a domain, type your question, and get an AI provisional answer while a senior reviews it."
        >
            {/* Domain selector */}
            <div className="fx-glass fx-reveal">
                <h3 className="fx-section-title">Select domain</h3>
                {userDomains.length === 0 ? (
                    <p style={{ color: '#666', fontSize: 14 }}>Add domains from your dashboard to ask questions.</p>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {userDomains.map((d) => (
                            <DomainBadge key={d.domain_id} domain={d} onClick={() => setSelectedDomain(d)} />
                        ))}
                    </div>
                )}
                {selectedDomain && (
                    <p style={{ fontSize: 13, color: '#999', marginTop: 8 }}>
                        Selected: <strong style={{ color: '#00b4d8' }}>{selectedDomain.name || selectedDomain.domain_name}</strong>
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
                    <button type="submit" disabled={loading || !content.trim() || !selectedDomain} className="btn-primary">
                        {loading ? 'Submitting...' : 'Submit Question'}
                    </button>
                </form>
            </div>

            {/* Polling */}
            {polling && (
                <div className="fx-glass" style={{ textAlign: 'center' }}>
                    <p style={{ color: '#999', fontSize: 13, margin: 0 }}>⏳ Waiting for senior response... (polling every 10s)</p>
                </div>
            )}
            {timeoutMsg && <p className="msg-error" style={{ marginBottom: 16 }}>{timeoutMsg}</p>}

            {/* Active query */}
            {activeQuery && (
                <div className="fx-reveal">
                    <h3 className="fx-section-title">Your Query</h3>
                    <QueryCard query={activeQuery} />
                </div>
            )}
        </EffectsLayout>
    );
}
