import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import {
    getUserThreads,
    getThread,
    sendMessage,
    getSeniorPendingRequests,
    acceptRequest,
    rejectRequest,
} from '../api/messaging';
import MessageRequestCard from '../components/MessageRequestCard';
import ThreadWindow from '../components/ThreadWindow';

/**
 * MessagingPage — view threads, manage requests (senior), send/receive messages.
 */
export default function MessagingPage() {
    const user = useAuthStore((s) => s.user);
    const userId = useAuthStore((s) => s.userId);

    const [threads, setThreads] = useState([]);
    const [selectedThread, setSelectedThread] = useState(null);
    const [pendingRequests, setPendingRequests] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!userId) return;
        setLoading(true);

        const fetchData = async () => {
            try {
                const threadData = await getUserThreads(userId);
                setThreads(Array.isArray(threadData) ? threadData : []);
            } catch {
                setThreads([]);
            }

            if (user?.role === 'SENIOR') {
                try {
                    const reqData = await getSeniorPendingRequests(userId);
                    setPendingRequests(Array.isArray(reqData) ? reqData : []);
                } catch {
                    setPendingRequests([]);
                }
            }

            setLoading(false);
        };

        fetchData();
    }, [userId, user?.role]);

    const handleSelectThread = async (threadSummary) => {
        try {
            const fullThread = await getThread(threadSummary.thread_id);
            setSelectedThread(fullThread);
        } catch {
            // silently fail
        }
    };

    const handleSend = async (content) => {
        if (!selectedThread || !userId) return;
        try {
            const newMsg = await sendMessage(selectedThread.thread_id, {
                sender_id: userId,
                content,
            });
            setSelectedThread((prev) => ({
                ...prev,
                messages: [...(prev.messages || []), newMsg],
            }));
        } catch {
            // silently fail
        }
    };

    const handleAccept = async (requestId) => {
        try {
            const newThread = await acceptRequest(requestId);
            setPendingRequests((prev) => prev.filter((r) => r.id !== requestId));
            setThreads((prev) => [
                {
                    thread_id: newThread.thread_id,
                    other_user_name: 'New thread',
                    last_message: '',
                    last_timestamp: new Date().toISOString(),
                    unread_count: 0,
                },
                ...prev,
            ]);
        } catch {
            // silently fail
        }
    };

    const handleReject = async (requestId) => {
        try {
            await rejectRequest(requestId);
            setPendingRequests((prev) => prev.filter((r) => r.id !== requestId));
        } catch {
            // silently fail
        }
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
            <div style={{ maxWidth: 1100, margin: '2rem auto', padding: '0 16px' }}>
                <h2>Messages 💬</h2>
                <p style={{ color: '#9ca3af' }}>Loading...</p>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: 1100, margin: '2rem auto', padding: '0 16px' }}>
            <h2>Messages 💬</h2>

            {/* Pending requests (senior only) */}
            {user?.role === 'SENIOR' && pendingRequests.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                    <h3>Pending Requests ({pendingRequests.length})</h3>
                    {pendingRequests.map((req) => (
                        <MessageRequestCard
                            key={req.id}
                            request={req}
                            onAccept={handleAccept}
                            onReject={handleReject}
                        />
                    ))}
                </div>
            )}

            <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
                {/* Thread list */}
                <div style={{ flex: '0 0 280px' }}>
                    <h3 style={{ marginTop: 0 }}>Conversations</h3>
                    {threads.length === 0 ? (
                        <p style={{ color: '#9ca3af', fontSize: 14 }}>No conversations yet.</p>
                    ) : (
                        threads.map((t) => (
                            <div
                                key={t.thread_id}
                                onClick={() => handleSelectThread(t)}
                                style={{
                                    padding: 12,
                                    borderRadius: 10,
                                    marginBottom: 6,
                                    cursor: 'pointer',
                                    background: selectedThread?.thread_id === t.thread_id ? '#eff6ff' : '#fff',
                                    border: `1px solid ${selectedThread?.thread_id === t.thread_id ? '#3b82f6' : '#e5e7eb'}`,
                                    transition: 'border-color 0.15s',
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontWeight: 600, fontSize: 14 }}>
                                        {t.other_user_name || 'Unknown'}
                                    </span>
                                    <span style={{ fontSize: 11, color: '#9ca3af' }}>
                                        {formatTime(t.last_timestamp)}
                                    </span>
                                </div>
                                <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>
                                    {(t.last_message || '').slice(0, 40)}{t.last_message?.length > 40 ? '…' : ''}
                                </p>
                                {t.unread_count > 0 && (
                                    <span
                                        style={{
                                            display: 'inline-block',
                                            marginTop: 4,
                                            padding: '1px 8px',
                                            borderRadius: 9999,
                                            fontSize: 11,
                                            fontWeight: 700,
                                            background: '#ef4444',
                                            color: '#fff',
                                        }}
                                    >
                                        {t.unread_count}
                                    </span>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Thread window */}
                <div style={{ flex: 1 }}>
                    {selectedThread ? (
                        <ThreadWindow
                            thread={selectedThread}
                            userId={userId}
                            onSend={handleSend}
                        />
                    ) : (
                        <div style={{ textAlign: 'center', paddingTop: 80, color: '#9ca3af' }}>
                            <p style={{ fontSize: 18 }}>Select a conversation to start messaging.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
