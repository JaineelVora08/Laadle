import React from 'react';

/**
 * ConflictAlert — shows red alert when conflicting senior advice is detected.
 * Props: { detected: bool, details: string | null }
 */
export default function ConflictAlert({ detected, details }) {
    if (!detected) return null;

    return (
        <div
            style={{
                background: '#fef2f2',
                border: '1px solid #ef4444',
                borderRadius: 12,
                padding: 16,
                marginTop: 12,
            }}
        >
            <h4 style={{ margin: '0 0 6px', color: '#b91c1c', fontSize: 15 }}>
                ⚠️ Conflict Detected in Senior Advice
            </h4>
            {details && (
                <p style={{ margin: '0 0 8px', color: '#1f2937', fontSize: 14 }}>{details}</p>
            )}
            <p style={{ margin: 0, color: '#6b7280', fontSize: 12, fontStyle: 'italic' }}>
                We've shown you both perspectives in the final answer.
            </p>
        </div>
    );
}
