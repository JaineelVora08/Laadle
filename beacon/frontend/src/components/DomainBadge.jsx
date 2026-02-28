import React from 'react';

const TYPE_COLORS = {
    TECHNICAL: '#00b4d8',
    ACADEMIC: '#22c55e',
    CAREER: '#f59e0b',
    SPORTS: '#ef4444',
    HOBBY: '#38bdf8',
    OTHER: '#6b7280',
};

/**
 * DomainBadge — dark pill-shaped badge with subtle glow on hover.
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
                padding: '5px 16px',
                borderRadius: 9999,
                fontSize: 13,
                fontWeight: 600,
                color: color,
                backgroundColor: `${color}15`,
                border: `1px solid ${color}30`,
                cursor: onClick ? 'pointer' : 'default',
                userSelect: 'none',
                transition: 'all 0.2s ease',
                margin: '4px 4px',
            }}
            onMouseEnter={onClick ? (e) => {
                e.target.style.boxShadow = `0 0 12px ${color}25`;
                e.target.style.transform = 'translateY(-1px)';
            } : undefined}
            onMouseLeave={onClick ? (e) => {
                e.target.style.boxShadow = 'none';
                e.target.style.transform = 'translateY(0)';
            } : undefined}
        >
            {domain?.name || domain?.domain_name || 'Unknown'}
        </span>
    );
}
