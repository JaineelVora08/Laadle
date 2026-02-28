import React from 'react';

/**
 * ConflictAlert — dark theme red alert card.
 */
export default function ConflictAlert({ detected, details }) {
    if (!detected) return null;

    return (
        <div
            style={{
                background: 'var(--error-dim)',
                border: '1px solid rgba(239,68,68,0.2)',
                borderRadius: 'var(--radius-md)',
                padding: 16,
                marginTop: 12,
            }}
        >
            <h4 style={{ margin: '0 0 6px', color: 'var(--error)', fontSize: 15 }}>
                ⚠️ Conflict Detected in Senior Advice
            </h4>
            {details && (
                <p style={{ margin: '0 0 8px', color: 'var(--text-primary)', fontSize: 14 }}>{details}</p>
            )}
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 12, fontStyle: 'italic' }}>
                We've shown you both perspectives in the final answer.
            </p>
        </div>
    );
}
