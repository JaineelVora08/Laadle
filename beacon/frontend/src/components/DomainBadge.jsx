import React from 'react';

const TYPE_COLORS = {
    TECHNICAL: '#3b82f6',
    ACADEMIC: '#22c55e',
    CAREER: '#f97316',
    SPORTS: '#ef4444',
    HOBBY: '#a855f7',
    OTHER: '#6b7280',
};

/**
 * DomainBadge — pill-shaped badge showing domain_name with color based on type.
 * Props: { domain, onClick }
 */
export default function DomainBadge({ domain, onClick }) {
    const color = TYPE_COLORS[domain?.type] || TYPE_COLORS.OTHER;

    return (
        <span
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={onClick ? (e) => { if (e.key === 'Enter') onClick(); } : undefined}
            style={{
                display: 'inline-block',
                padding: '4px 14px',
                borderRadius: 9999,
                fontSize: 13,
                fontWeight: 600,
                color: '#fff',
                backgroundColor: color,
                cursor: onClick ? 'pointer' : 'default',
                userSelect: 'none',
                transition: 'opacity 0.15s',
                margin: '4px 4px',
            }}
        >
            {domain?.domain_name || 'Unknown'}
        </span>
    );
}
