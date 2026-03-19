import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { completeSeniorOnboarding } from '../api/profile';
import EffectsLayout from '../components/EffectsLayout';

/**
 * SeniorOnboardingPage — mandatory profile completion for new seniors.
 * Collects: current_level, at least 1 domain, at least 1 achievement.
 */
export default function SeniorOnboardingPage() {
    const navigate = useNavigate();
    const userId = useAuthStore((s) => s.userId);
    const hydrateProfile = useAuthStore((s) => s.hydrateProfile);

    const [currentLevel, setCurrentLevel] = useState('');
    const [domains, setDomains] = useState(['']);
    const [achievements, setAchievements] = useState([{ title: '', proof_url: '' }]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Domain helpers
    const addDomainField = () => setDomains((prev) => [...prev, '']);
    const updateDomain = (i, value) => setDomains((prev) => prev.map((d, idx) => (idx === i ? value : d)));
    const removeDomain = (i) => {
        if (domains.length <= 1) return;
        setDomains((prev) => prev.filter((_, idx) => idx !== i));
    };

    // Achievement helpers
    const addAchievementField = () => setAchievements((prev) => [...prev, { title: '', proof_url: '' }]);
    const updateAchievement = (i, field, value) =>
        setAchievements((prev) => prev.map((a, idx) => (idx === i ? { ...a, [field]: value } : a)));
    const removeAchievement = (i) => {
        if (achievements.length <= 1) return;
        setAchievements((prev) => prev.filter((_, idx) => idx !== i));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Client-side validation
        const validDomains = domains.map((d) => d.trim()).filter(Boolean);
        const validAchievements = achievements.filter((a) => a.title.trim() && a.proof_url.trim());

        if (!currentLevel.trim()) {
            setError('Please enter your current level (e.g. 3rd Year B.Tech).');
            return;
        }
        if (validDomains.length === 0) {
            setError('Please add at least one domain of expertise.');
            return;
        }
        if (validAchievements.length === 0) {
            setError('Please add at least one achievement with a proof URL.');
            return;
        }
        if (achievements.some((a) => a.title.trim() && !a.proof_url.trim())) {
            setError('Proof URL is required for every achievement.');
            return;
        }

        setLoading(true);
        try {
            await completeSeniorOnboarding(userId, {
                current_level: currentLevel.trim(),
                domains: validDomains,
                achievements: validAchievements.map((a) => ({
                    title: a.title.trim(),
                    proof_url: a.proof_url.trim(),
                })),
            });
            await hydrateProfile();
            navigate('/dashboard/senior');
        } catch (err) {
            const d = err?.response?.data;
            if (d && typeof d === 'object') {
                const msgs = Object.values(d).flat();
                setError(msgs.join(' '));
            } else {
                setError('Onboarding failed. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <EffectsLayout
            title="Complete Your Profile"
            tagline="Help juniors find the right mentor — tell us about your expertise."
            auroraColors={['#00b4d8', '#0077b6', '#023e8a']}
        >
            <form onSubmit={handleSubmit}>
                {/* Current Level */}
                <div className="fx-glass fx-reveal">
                    <h3 className="fx-section-title">Basic Info</h3>
                    <label style={{ color: '#8a8a8a', fontSize: 13, display: 'block', marginBottom: 6 }}>
                        Current Level *
                    </label>
                    <input
                        type="text"
                        placeholder="e.g. 3rd Year B.Tech, M.Tech 1st Year"
                        value={currentLevel}
                        onChange={(e) => setCurrentLevel(e.target.value)}
                        className="dark-input"
                        style={{ width: '100%' }}
                        required
                    />
                </div>

                {/* Domains */}
                <div className="fx-glass fx-reveal">
                    <h3 className="fx-section-title">Domains of Expertise *</h3>
                    <p style={{ color: '#8a8a8a', fontSize: 13, marginBottom: 12 }}>
                        Add at least one domain you can mentor in (e.g. Machine Learning, Web Development).
                    </p>
                    {domains.map((domain, i) => (
                        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                            <input
                                type="text"
                                placeholder={`Domain ${i + 1}`}
                                value={domain}
                                onChange={(e) => updateDomain(i, e.target.value)}
                                className="dark-input"
                                style={{ flex: 1 }}
                            />
                            {domains.length > 1 && (
                                <button
                                    type="button"
                                    onClick={() => removeDomain(i)}
                                    style={{
                                        background: 'rgba(239,68,68,0.15)',
                                        color: '#ef4444',
                                        border: '1px solid rgba(239,68,68,0.3)',
                                        borderRadius: 8,
                                        padding: '6px 12px',
                                        cursor: 'pointer',
                                        fontSize: 13,
                                    }}
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={addDomainField}
                        className="btn-secondary"
                        style={{ fontSize: 13, padding: '6px 16px', marginTop: 4 }}
                    >
                        + Add another domain
                    </button>
                </div>

                {/* Achievements */}
                <div className="fx-glass fx-reveal">
                    <h3 className="fx-section-title">Achievements *</h3>
                    <p style={{ color: '#8a8a8a', fontSize: 13, marginBottom: 12 }}>
                        Add at least one achievement or credential (e.g. project, certification, competition win).
                    </p>
                    {achievements.map((ach, i) => (
                        <div
                            key={i}
                            style={{
                                padding: 14,
                                background: 'rgba(255,255,255,0.03)',
                                border: '1px solid rgba(255,255,255,0.06)',
                                borderRadius: 10,
                                marginBottom: 10,
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <span style={{ color: '#8a8a8a', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
                                    Achievement {i + 1}
                                </span>
                                {achievements.length > 1 && (
                                    <button
                                        type="button"
                                        onClick={() => removeAchievement(i)}
                                        style={{
                                            background: 'none',
                                            color: '#ef4444',
                                            border: 'none',
                                            cursor: 'pointer',
                                            fontSize: 13,
                                        }}
                                    >
                                        Remove
                                    </button>
                                )}
                            </div>
                            <input
                                type="text"
                                placeholder="Title (e.g. Built a RAG chatbot)"
                                value={ach.title}
                                onChange={(e) => updateAchievement(i, 'title', e.target.value)}
                                className="dark-input"
                                style={{ width: '100%', marginBottom: 8 }}
                            />
                            <input
                                type="url"
                                placeholder="Proof URL (required)"
                                value={ach.proof_url}
                                onChange={(e) => updateAchievement(i, 'proof_url', e.target.value)}
                                className="dark-input"
                                style={{ width: '100%' }}
                                required
                            />
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={addAchievementField}
                        className="btn-secondary"
                        style={{ fontSize: 13, padding: '6px 16px', marginTop: 4 }}
                    >
                        + Add another achievement
                    </button>
                </div>

                {/* Error */}
                {error && (
                    <p style={{ color: '#ef4444', fontSize: 14, marginTop: 12, marginBottom: 0 }}>
                        {error}
                    </p>
                )}

                {/* Submit */}
                <button
                    type="submit"
                    className="btn-primary"
                    disabled={loading}
                    style={{ width: '100%', padding: '14px', fontSize: 16, marginTop: 16 }}
                >
                    {loading ? 'Saving...' : 'Complete Profile & Enter Dashboard →'}
                </button>
            </form>
        </EffectsLayout>
    );
}
