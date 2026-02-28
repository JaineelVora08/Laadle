import React, { useState, useRef, useEffect } from 'react';

/**
 * ThreadWindow — dark theme chat window with glass styling.
 */
export default function ThreadWindow({ thread, userId, onSend }) {
    const [input, setInput] = useState('');
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [thread?.messages]);

    if (!thread) return null;

    const handleSend = () => {
        if (!input.trim()) return;
        onSend(input.trim());
        setInput('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const formatTime = (ts) => {
        const d = new Date(ts);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div
            style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                minHeight: 400,
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                overflow: 'hidden',
                background: 'var(--bg-card)',
            }}
        >
            {/* Messages area */}
            <div
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: 16,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                }}
            >
                {(thread.messages || []).map((msg) => {
                    const isMine = msg.sender_id === userId;
                    return (
                        <div
                            key={msg.id}
                            style={{
                                alignSelf: isMine ? 'flex-end' : 'flex-start',
                                maxWidth: '70%',
                            }}
                        >
                            <div
                                style={{
                                    padding: '8px 14px',
                                    borderRadius: 16,
                                    background: isMine
                                        ? 'linear-gradient(135deg, #00b4d8, #0096b7)'
                                        : 'rgba(255,255,255,0.06)',
                                    color: isMine ? '#fff' : 'var(--text-primary)',
                                    fontSize: 14,
                                    lineHeight: 1.5,
                                    wordBreak: 'break-word',
                                    border: isMine ? 'none' : '1px solid var(--border-subtle)',
                                }}
                            >
                                {msg.content}
                            </div>
                            <p
                                style={{
                                    margin: '2px 4px 0',
                                    fontSize: 11,
                                    color: 'var(--text-muted)',
                                    textAlign: isMine ? 'right' : 'left',
                                }}
                            >
                                {formatTime(msg.timestamp)}
                            </p>
                        </div>
                    );
                })}
                <div ref={bottomRef} />
            </div>

            {/* Input area */}
            <div
                style={{
                    display: 'flex',
                    gap: 8,
                    padding: 12,
                    borderTop: '1px solid var(--border-subtle)',
                    background: 'var(--bg-secondary)',
                }}
            >
                <input
                    type="text"
                    placeholder="Type a message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="dark-input"
                    style={{ flex: 1 }}
                />
                <button
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className="btn-primary"
                    style={{ padding: '8px 20px' }}
                >
                    Send
                </button>
            </div>
        </div>
    );
}
