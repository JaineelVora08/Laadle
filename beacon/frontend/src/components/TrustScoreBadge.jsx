import React from 'react';

/**
 * TrustScoreBadge — circular badge showing trust score as percentage.
 * Props: { score: float 0 to 1 }
 */
export default function TrustScoreBadge({ score }) {
    const pct = Math.round((score || 0) * 100);
    let color = '#ef4444'; // red
    if (score >= 0.8) color = '#22c55e'; // green
    else if (score >= 0.5) color = '#eab308'; // yellow

    const radius = 20;
    const circumference = 2 * Math.PI * radius;
    const dashOffset = circumference * (1 - (score || 0));

    return (
        <span
            title="Trust Score based on feedback, consistency, and achievements"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, cursor: 'help' }}
        >
            <svg width="48" height="48" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="4" />
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
                    style={{ transition: 'stroke-dashoffset 0.4s ease' }}
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
