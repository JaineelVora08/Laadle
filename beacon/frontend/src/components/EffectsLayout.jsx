import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import Aurora from './Aurora';
import './EffectsLayout.css';

/**
 * EffectsLayout — Wraps any page with Aurora hero, particles,
 * mouse spotlight, RepelText heading, WaveText tagline, and
 * scroll-reveal support.
 *
 * Usage:
 * <EffectsLayout title="Welcome" tagline="Subtitle text">
 *   <div className="fx-content">
 *     <div className="fx-glass fx-reveal">...</div>
 *   </div>
 * </EffectsLayout>
 */
export default function EffectsLayout({ title, tagline, children, auroraColors }) {
    const [mousePos, setMousePos] = useState({ x: -500, y: -500 });
    const revealRefs = useRef([]);

    const handleMouseMove = useCallback((e) => {
        setMousePos({ x: e.clientX, y: e.clientY });
    }, []);

    useEffect(() => {
        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, [handleMouseMove]);

    // Scroll-reveal observer
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                    }
                });
            },
            { threshold: 0.1 }
        );

        // Observe all .fx-reveal elements in the page
        const els = document.querySelectorAll('.fx-reveal');
        els.forEach((el) => observer.observe(el));

        return () => observer.disconnect();
    });

    // Particles (memoized)
    const particles = useMemo(() =>
        Array.from({ length: 20 }, (_, i) => ({
            id: i,
            left: `${Math.random() * 100}%`,
            size: Math.random() * 2 + 1,
            duration: Math.random() * 15 + 10,
            delay: Math.random() * 15,
            opacity: Math.random() * 0.4 + 0.15,
        })), []
    );

    const colors = auroraColors || ["#00b4d8", "#0077b6", "#023e8a"];

    return (
        <div className="fx-page">
            {/* Particles */}
            <div className="fx-particles">
                {particles.map((p) => (
                    <div
                        key={p.id}
                        className="fx-particle"
                        style={{
                            left: p.left,
                            width: p.size,
                            height: p.size,
                            animationDuration: `${p.duration}s`,
                            animationDelay: `${p.delay}s`,
                            opacity: p.opacity,
                        }}
                    />
                ))}
            </div>

            {/* Mouse spotlight */}
            <div className="fx-spotlight" style={{ left: mousePos.x, top: mousePos.y }} />

            {/* Hero section with Aurora */}
            <div className="fx-hero">
                <Aurora
                    colorStops={colors}
                    blend={0.6}
                    amplitude={1.2}
                    speed={0.8}
                />
                <div className="fx-hero-overlay" />

                <div className="fx-hero-content">
                    <RepelText text={title} mousePos={mousePos} className="fx-heading" tag="h1" />
                    {tagline && <WaveText text={tagline} className="fx-tagline" />}
                </div>
            </div>

            {/* Page content */}
            <div className="fx-content">
                {children}
            </div>
        </div>
    );
}

/**
 * RepelText — each letter pushes away from the mouse cursor.
 */
export function RepelText({ text, mousePos, className, tag: Tag = 'h1' }) {
    const containerRef = useRef(null);
    const letterRefs = useRef([]);
    const rafRef = useRef(null);
    const positionsRef = useRef([]);

    useEffect(() => {
        positionsRef.current = text.split('').map(() => ({ x: 0, y: 0 }));
    }, [text]);

    useEffect(() => {
        const animate = () => {
            letterRefs.current.forEach((el, i) => {
                if (!el) return;

                const rect = el.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                const dx = cx - mousePos.x;
                const dy = cy - mousePos.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                const maxDist = 220;
                const maxPush = 45;
                let tx = 0, ty = 0;

                if (dist < maxDist && dist > 0) {
                    const force = (1 - dist / maxDist) * maxPush;
                    tx = (dx / dist) * force;
                    ty = (dy / dist) * force;
                }

                const curr = positionsRef.current[i] || { x: 0, y: 0 };
                curr.x += (tx - curr.x) * 0.15;
                curr.y += (ty - curr.y) * 0.15;
                positionsRef.current[i] = curr;
                el.style.transform = `translate(${curr.x}px, ${curr.y}px)`;
            });

            rafRef.current = requestAnimationFrame(animate);
        };

        rafRef.current = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(rafRef.current);
    }, [mousePos, text]);

    return (
        <Tag className={className} ref={containerRef}>
            {text.split('').map((char, i) => (
                <span
                    key={i}
                    ref={(el) => { letterRefs.current[i] = el; }}
                    style={{
                        display: 'inline-block',
                        willChange: 'transform',
                        whiteSpace: char === ' ' ? 'pre' : 'normal',
                    }}
                >
                    {char === ' ' ? '\u00A0' : char}
                </span>
            ))}
        </Tag>
    );
}

/**
 * WaveText — each letter has a staggered wave animation.
 */
export function WaveText({ text, className }) {
    return (
        <p className={className} style={{ overflow: 'visible' }}>
            {text.split('').map((char, i) => (
                <span
                    key={i}
                    style={{
                        display: 'inline-block',
                        animation: `fxWaveChar 3s ease-in-out ${i * 0.06}s infinite`,
                        whiteSpace: char === ' ' ? 'pre' : 'normal',
                    }}
                >
                    {char === ' ' ? '\u00A0' : char}
                </span>
            ))}
        </p>
    );
}
