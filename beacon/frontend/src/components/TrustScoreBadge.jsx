import React from 'react';

/**
 * TrustScoreBadge — circular SVG badge, dark theme colors.
 */
export default function TrustScoreBadge({ score }) {
    const pct = Math.round((score || 0) * 100);
    let color = '#ef4444';
    if (score >= 0.8) color = '#22c55e';
    else if (score >= 0.5) color = '#f59e0b';

    const radius = 20;
    const circumference = 2 * Math.PI * radius;
    const dashOffset = circumference * (1 - (score || 0));

    return (
        <span
            title="Trust Score based on feedback, consistency, and achievements"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, cursor: 'help' }}
        >
            <svg width="48" height="48" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
                <circle
                    cx="24"
                    cy="24"
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={dashOffset}
                    transform="rotate(-90 24 24)"
                    style={{
                        transition: 'stroke-dashoffset 0.6s ease',
                        filter: `drop-shadow(0 0 4px ${color}50)`,
                    }}
                />
                <text
                    x="24"
                    y="24"
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize="12"
                    fontWeight="700"
                    fill={color}
                >
                    {pct}%
                </text>
            </svg>
        </span>
    );
}
