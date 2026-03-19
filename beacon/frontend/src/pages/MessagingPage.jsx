import React, { useEffect, useState, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import {
    getThreadsAndPending,
    getThread,
    sendMessage,
    acceptRequest,
    rejectRequest,
} from '../api/messaging';
import MessageRequestCard from '../components/MessageRequestCard';
import ThreadWindow from '../components/ThreadWindow';
import EffectsLayout from '../components/EffectsLayout';

export default function MessagingPage() {
    const user = useAuthStore((s) => s.user);
    const userId = useAuthStore((s) => s.userId);

    const [threads, setThreads] = useState([]);
    const [selectedThread, setSelectedThread] = useState(null);
    const [pendingRequests, setPendingRequests] = useState([]);
    const [sentRequests, setSentRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingThread, setLoadingThread] = useState(false);

    // Single combined fetch on mount — no redundant API calls
    useEffect(() => {
        if (!userId) return;
        setLoading(true);

        getThreadsAndPending(userId, user?.role)
            .then(({ threads: t, pendingRequests: p, sentRequests: s }) => {
                setThreads(t);
                setPendingRequests(p);
                setSentRequests(s || []);
            })
            .catch(() => {
                setThreads([]);
                setPendingRequests([]);
                setSentRequests([]);
            })
            .finally(() => setLoading(false));
    }, [userId, user?.role]);

    const handleSelectThread = useCallback(async (threadSummary) => {
        // Show thread selection immediately (keeps previous messages if re-selecting)
        if (selectedThread?.thread_id === threadSummary.thread_id) return;

        setLoadingThread(true);
        try {
            const fullThread = await getThread(threadSummary.thread_id);
            setSelectedThread(fullThread);
        } catch { /* silently fail */ }
        finally { setLoadingThread(false); }
    }, [selectedThread?.thread_id]);

    // Optimistic send — show message immediately, confirm with server
    const handleSend = useCallback(async (content) => {
        if (!selectedThread || !userId) return;

        // Create optimistic message
        const optimisticMsg = {
            id: `temp-${Date.now()}`,
            sender_id: userId,
            content,
            timestamp: new Date().toISOString(),
            _pending: true,
        };

        // Show it immediately
        setSelectedThread((prev) => ({
            ...prev,
            messages: [...(prev.messages || []), optimisticMsg],
        }));

        try {
            const confirmedMsg = await sendMessage(selectedThread.thread_id, {
                sender_id: userId,
                content,
            });
            // Replace optimistic message with server-confirmed one
            setSelectedThread((prev) => ({
                ...prev,
                messages: (prev.messages || []).map((m) =>
                    m.id === optimisticMsg.id ? { ...confirmedMsg, _pending: false } : m
                ),
            }));
        } catch {
            // Mark as failed
            setSelectedThread((prev) => ({
                ...prev,
                messages: (prev.messages || []).map((m) =>
                    m.id === optimisticMsg.id ? { ...m, _failed: true, _pending: false } : m
                ),
            }));
        }
    }, [selectedThread, userId]);

    const handleAccept = async (requestId) => {
        try {
            const newThread = await acceptRequest(requestId);
            setPendingRequests((prev) => prev.filter((r) => r.id !== requestId));
            setThreads((prev) => [{
                thread_id: newThread.thread_id,
                other_user_name: 'New thread',
                last_message: '',
                last_timestamp: new Date().toISOString(),
                unread_count: 0,
            }, ...prev]);
        } catch { /* silently fail */ }
    };

    const handleReject = async (requestId) => {
        try {
            await rejectRequest(requestId);
            setPendingRequests((prev) => prev.filter((r) => r.id !== requestId));
        } catch { /* silently fail */ }
    };

    const formatTime = (ts) => {
        if (!ts) return '';
        const d = new Date(ts);
        const now = new Date();
        if (d.toDateString() === now.toDateString()) {
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        return d.toLocaleDateString();
    };

    if (loading) {
        return (
            <EffectsLayout title="Messages 💬" tagline="Loading...">
                <p style={{ color: '#666' }}>Loading conversations...</p>
            </EffectsLayout>
        );
    }

    return (
        <EffectsLayout title="Messages 💬" tagline="Chat with mentors and students.">
            {/* Pending requests (senior only) */}
            {user?.role === 'SENIOR' && pendingRequests.length > 0 && (
                <div className="fx-reveal" style={{ marginBottom: 24 }}>
                    <h3 className="fx-section-title">Pending Requests ({pendingRequests.length})</h3>
                    {pendingRequests.map((req) => (
                        <MessageRequestCard key={req.id} request={req} onAccept={handleAccept} onReject={handleReject} />
                    ))}
                </div>
            )}

            {/* Sent requests (student only) — shows pending connect requests */}
            {user?.role === 'STUDENT' && sentRequests.length > 0 && (
                <div className="fx-reveal" style={{ marginBottom: 24 }}>
                    <h3 className="fx-section-title">Sent Requests ({sentRequests.length})</h3>
                    {sentRequests.map((req) => (
                        <div key={req.id} className="glass-card-static" style={{ padding: 16, marginBottom: 10 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <h4 style={{ margin: 0, fontSize: 15, color: 'var(--text-primary)' }}>{req.other_user_name}</h4>
                                    <p style={{ margin: '4px 0', color: 'var(--text-muted)', fontSize: 13 }}>
                                        {req.domain_name ? `${req.domain_name} • ` : ''}Waiting for response
                                    </p>
                                </div>
                                <span className="badge badge-pending" style={{ fontSize: 11 }}>Pending</span>
                            </div>
                            {req.preview_text && (
                                <p style={{ margin: '8px 0 0', fontSize: 13, color: 'var(--text-secondary)' }}>
                                    {req.preview_text.slice(0, 120)}{req.preview_text.length > 120 ? '…' : ''}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <div style={{ display: 'flex', gap: 24, marginTop: 8 }}>
                {/* Thread list */}
                <div style={{ flex: '0 0 280px' }}>
                    <h3 className="fx-section-title">Conversations</h3>
                    {threads.length === 0 ? (
                        <p style={{ color: '#666', fontSize: 14 }}>No conversations yet.</p>
                    ) : (
                        threads.map((t) => (
                            <div
                                key={t.thread_id}
                                onClick={() => handleSelectThread(t)}
                                className={`list-item ${selectedThread?.thread_id === t.thread_id ? 'active' : ''}`}
                                style={{ cursor: 'pointer' }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontWeight: 600, fontSize: 14, color: '#f0f0f0' }}>
                                        {t.other_user_name || 'Unknown'}
                                    </span>
                                    <span style={{ fontSize: 11, color: '#666' }}>{formatTime(t.last_timestamp)}</span>
                                </div>
                                <p style={{ margin: '4px 0 0', fontSize: 13, color: '#999' }}>
                                    {(t.last_message || '').slice(0, 40)}{t.last_message?.length > 40 ? '…' : ''}
                                </p>
                                {t.unread_count > 0 && (
                                    <span style={{
                                        display: 'inline-block', marginTop: 4, padding: '1px 8px',
                                        borderRadius: 9999, fontSize: 11, fontWeight: 700,
                                        background: '#ef4444', color: '#fff',
                                    }}>
                                        {t.unread_count}
                                    </span>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Thread window */}
                <div style={{ flex: 1 }}>
                    {loadingThread ? (
                        <div style={{ textAlign: 'center', paddingTop: 80, color: '#666' }}>
                            <div style={{
                                width: 28, height: 28,
                                border: '3px solid var(--accent)',
                                borderTop: '3px solid transparent',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                                margin: '0 auto 12px',
                            }} />
                            <p style={{ fontSize: 14 }}>Loading messages...</p>
                            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                        </div>
                    ) : selectedThread ? (
                        <ThreadWindow thread={selectedThread} userId={userId} onSend={handleSend} />
                    ) : (
                        <div style={{ textAlign: 'center', paddingTop: 80, color: '#666' }}>
                            <p style={{ fontSize: 18 }}>Select a conversation to start messaging.</p>
                        </div>
                    )}
                </div>
            </div>
        </EffectsLayout>
    );
}
