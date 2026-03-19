import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useQueryStore } from '../store/queryStore';
import { getUserDomains, addDomain } from '../api/domains';
import DomainBadge from '../components/DomainBadge';
import QueryCard from '../components/QueryCard';
import Aurora from '../components/Aurora';
import './StudentDashboard.css';

/**
 * StudentDashboard — Aurora WebGL background, mouse spotlight,
 * particles, scroll-reveal, 3D tilt cards, animated text.
 */
export default function StudentDashboard() {
    const user = useAuthStore((s) => s.user);
    const userId = useAuthStore((s) => s.userId);
    const queries = useQueryStore((s) => s.queries);

    const [domains, setDomains] = useState([]);
    const [newDomain, setNewDomain] = useState('');
    const [loading, setLoading] = useState(true);
    const [addingDomain, setAddingDomain] = useState(false);
    const [mousePos, setMousePos] = useState({ x: -500, y: -500 });

    const revealRefs = useRef([]);

    useEffect(() => {
        if (!userId) return;
        setLoading(true);
        getUserDomains(userId)
            .then((data) => setDomains(Array.isArray(data) ? data : []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [userId]);

    // Mouse spotlight
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
            { threshold: 0.15 }
        );
        revealRefs.current.forEach((el) => { if (el) observer.observe(el); });
        return () => observer.disconnect();
    }, [domains, queries]);

    const addRevealRef = (el) => {
        if (el && !revealRefs.current.includes(el)) {
            revealRefs.current.push(el);
        }
    };

    const handleAddDomain = async (e) => {
        e.preventDefault();
        if (!newDomain.trim() || !userId) return;
        setAddingDomain(true);
        try {
            const result = await addDomain({ user_id: userId, raw_interest_text: newDomain.trim() });
            setDomains((prev) =>
                prev.some((d) => d.domain_id === result.domain_id) ? prev : [...prev, result]
            );
            setNewDomain('');
        } catch {
            // silently fail
        } finally {
            setAddingDomain(false);
        }
    };

    const recentQueries = queries.slice(-3).reverse();

    // Particles
    const particles = Array.from({ length: 25 }, (_, i) => ({
        id: i,
        left: `${Math.random() * 100}%`,
        size: Math.random() * 2 + 1,
        duration: Math.random() * 15 + 10,
        delay: Math.random() * 15,
        opacity: Math.random() * 0.4 + 0.15,
    }));

    return (
        <div className="sd-page">
            {/* Particles */}
            <div className="sd-particles">
                {particles.map((p) => (
                    <div
                        key={p.id}
                        className="sd-particle"
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
            <div className="sd-spotlight" style={{ left: mousePos.x, top: mousePos.y }} />

            {/* ===== HERO SECTION WITH AURORA ===== */}
            <div className="sd-hero-section">
                {/* Aurora WebGL background */}
                <Aurora
                    colorStops={["#00b4d8", "#0077b6", "#023e8a"]}
                    blend={0.6}
                    amplitude={1.2}
                    speed={0.8}
                />

                {/* Dark overlay for text readability */}
                <div className="sd-hero-overlay" />

                {/* Hero text — letters repel from mouse */}
                <div className="sd-hero-content">
                    <RepelText
                        text={`Welcome, ${user?.name || 'Student'} 👋`}
                        mousePos={mousePos}
                        className="sd-heading"
                        tag="h1"
                    />
                    <WaveText
                        text="Guiding you through campus fog."
                        className="sd-tagline"
                    />
                    <div className="sd-hero-actions">
                        <Link to="/query" className="sd-hero-btn sd-hero-btn-primary">
                            Ask a Question
                        </Link>
                        <Link to="/mentor-match" className="sd-hero-btn sd-hero-btn-ghost">
                            Find Matches
                        </Link>
                    </div>
                </div>

                {/* Scroll indicator */}
                <div className="sd-scroll-hint">
                    <span>Scroll</span>
                    <div className="sd-scroll-arrow" />
                </div>
            </div>

            {/* ===== DASHBOARD CONTENT ===== */}
            <div className="sd-content">
                {/* Stats */}
                <div className="sd-stats sd-reveal" ref={addRevealRef}>
                    <div className="sd-stat-box">
                        <AnimatedCounter value={domains.length} />
                        <p className="sd-stat-label">Domains</p>
                    </div>
                    <div className="sd-stat-box">
                        <AnimatedCounter value={recentQueries.length} />
                        <p className="sd-stat-label">Recent Queries</p>
                    </div>
                    <div className="sd-stat-box">
                        <AnimatedCounter value={queries.length} />
                        <p className="sd-stat-label">Total Queries</p>
                    </div>
                </div>

                {/* Domains */}
                <div className="sd-glass sd-reveal" ref={addRevealRef}>
                    <h3 className="sd-section-title">Your Domains</h3>
                    {loading ? (
                        <p style={{ color: '#555' }}>Loading domains...</p>
                    ) : domains.length === 0 ? (
                        <p style={{ color: '#555' }}>No domains yet. Add one below!</p>
                    ) : (
                        <div className="sd-domain-area">
                            {domains.map((d) => (
                                <DomainBadge key={d.domain_id} domain={d} />
                            ))}
                        </div>
                    )}
                    <form onSubmit={handleAddDomain} className="sd-add-form">
                        <input
                            type="text"
                            placeholder="Add a domain (e.g. Machine Learning)"
                            value={newDomain}
                            onChange={(e) => setNewDomain(e.target.value)}
                            className="sd-add-input"
                        />
                        <button
                            type="submit"
                            disabled={addingDomain || !newDomain.trim()}
                            className="sd-add-btn"
                        >
                            {addingDomain ? 'Adding...' : '+ Add'}
                        </button>
                    </form>
                </div>

                {/* Quick Links — 3D tilt cards */}
                <div className="sd-reveal" ref={addRevealRef}>
                    <h3 className="sd-section-title">Quick Actions</h3>
                    <div className="sd-links">
                        <TiltCard to="/mentor-match" icon="🎯" label="Find Matches" desc="Match with seniors or peers" />
                        <TiltCard to="/query" icon="❓" label="Ask a Question" desc="Get AI + senior answers" />
                        <TiltCard to="/messages" icon="💬" label="Messages" desc="Chat with mentors" />
                    </div>
                </div>

                {/* Recent Queries */}
                {recentQueries.length > 0 && (
                    <div className="sd-reveal" ref={addRevealRef}>
                        <h3 className="sd-section-title">Recent Queries</h3>
                        {recentQueries.map((q) => (
                            <QueryCard key={q.query_id} query={q} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

/** 3D tilt card with glow spot tracking */
function TiltCard({ to, icon, label, desc }) {
    const cardRef = useRef(null);
    const glowRef = useRef(null);

    const handleMouseMove = (e) => {
        const card = cardRef.current;
        const glow = glowRef.current;
        if (!card || !glow) return;

        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        card.style.transform = `perspective(600px) rotateX(${((y - centerY) / centerY) * -10}deg) rotateY(${((x - centerX) / centerX) * 10}deg) translateY(-4px)`;
        glow.style.left = `${x}px`;
        glow.style.top = `${y}px`;
    };

    const handleMouseLeave = () => {
        if (cardRef.current) cardRef.current.style.transform = '';
    };

    return (
        <Link to={to} className="sd-tilt-card" ref={cardRef} onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave}>
            <div className="tilt-glow" ref={glowRef} />
            <div className="tilt-icon">{icon}</div>
            <div>
                <div className="tilt-label">{label}</div>
                <div className="tilt-desc">{desc}</div>
            </div>
        </Link>
    );
}

/** Animated counter — starts when scrolled into view */
function AnimatedCounter({ value }) {
    const [display, setDisplay] = useState(0);
    const ref = useRef(null);
    const [started, setStarted] = useState(false);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => { if (entry.isIntersecting) setStarted(true); },
            { threshold: 0.5 }
        );
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        if (!started || value === 0) { setDisplay(value); return; }
        let start = 0;
        const step = Math.max(1, Math.floor(1200 / value));
        const interval = setInterval(() => {
            start += 1;
            setDisplay(start);
            if (start >= value) { clearInterval(interval); setDisplay(value); }
        }, step);
        return () => clearInterval(interval);
    }, [value, started]);

    return <p className="sd-stat-value" ref={ref}>{display}</p>;
}

/**
 * RepelText — each letter pushes away from the mouse cursor.
 * The closer the mouse, the more each letter is displaced.
 */
function RepelText({ text, mousePos, className, tag: Tag = 'h1' }) {
    const containerRef = useRef(null);
    const letterRefs = useRef([]);
    const rafRef = useRef(null);

    // Store current positions to smoothly interpolate
    const positionsRef = useRef([]);

    useEffect(() => {
        positionsRef.current = [...text].map(() => ({ x: 0, y: 0 }));
    }, [text]);

    useEffect(() => {
        const animate = () => {
            const container = containerRef.current;
            if (!container) return;

            letterRefs.current.forEach((el, i) => {
                if (!el) return;

                const rect = el.getBoundingClientRect();
                const letterCenterX = rect.left + rect.width / 2;
                const letterCenterY = rect.top + rect.height / 2;

                const dx = letterCenterX - mousePos.x;
                const dy = letterCenterY - mousePos.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                const maxDistance = 220; // radius of influence
                const maxDisplacement = 45; // max pixels to push

                let targetX = 0;
                let targetY = 0;

                if (distance < maxDistance && distance > 0) {
                    const force = (1 - distance / maxDistance) * maxDisplacement;
                    targetX = (dx / distance) * force;
                    targetY = (dy / distance) * force;
                }

                // Smooth lerp toward target
                const curr = positionsRef.current[i] || { x: 0, y: 0 };
                const lerpFactor = 0.15;
                curr.x += (targetX - curr.x) * lerpFactor;
                curr.y += (targetY - curr.y) * lerpFactor;
                positionsRef.current[i] = curr;

                el.style.transform = `translate(${curr.x}px, ${curr.y}px)`;
            });

            rafRef.current = requestAnimationFrame(animate);
        };

        rafRef.current = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(rafRef.current);
    }, [mousePos, text]);

    const letters = [...text];

    return (
        <Tag className={className} ref={containerRef}>
            {letters.map((char, i) => (
                <span
                    key={i}
                    ref={(el) => { letterRefs.current[i] = el; }}
                    style={{
                        display: 'inline-block',
                        transition: 'none',
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
 * WaveText — each letter has a staggered sine-wave animation.
 */
function WaveText({ text, className }) {
    const letters = [...text];

    return (
        <p className={className} style={{ overflow: 'visible' }}>
            {letters.map((char, i) => (
                <span
                    key={i}
                    style={{
                        display: 'inline-block',
                        animation: `waveChar 3s ease-in-out ${i * 0.06}s infinite`,
                        whiteSpace: char === ' ' ? 'pre' : 'normal',
                    }}
                >
                    {char === ' ' ? '\u00A0' : char}
                </span>
            ))}
            <style>{`
                @keyframes waveChar {
                    0%, 100% { transform: translateY(0); }
                    25% { transform: translateY(-4px); }
                    75% { transform: translateY(4px); }
                }
            `}</style>
        </p>
    );
}
