import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProfile, addAchievement, updateProfile } from '../api/profile';
import { sendMessageRequest } from '../api/messaging';
import { getUserDomains, addDomain } from '../api/domains';
import { useAuthStore } from '../store/authStore';
import EffectsLayout from '../components/EffectsLayout';
import TrustScoreBadge from '../components/TrustScoreBadge';
import DomainBadge from '../components/DomainBadge';

export default function ProfilePage() {
    const { userId: paramUserId } = useParams();
    const navigate = useNavigate();
    const loggedInUserId = useAuthStore((state) => state.userId);
    const loggedInUser = useAuthStore((state) => state.user);
    const hydrateProfile = useAuthStore((state) => state.hydrateProfile);
    const [connectStatus, setConnectStatus] = useState(null);

    // Determine whose profile we're viewing
    const targetUserId = paramUserId || loggedInUserId;
    const isOwnProfile = !paramUserId || paramUserId === loggedInUserId;

    const [viewedUser, setViewedUser] = useState(null);
    const [loadingProfile, setLoadingProfile] = useState(false);

    const [profileForm, setProfileForm] = useState({ name: '', current_level: '', availability: true });
    const [achievementForm, setAchievementForm] = useState({ title: '', proof_url: '' });
    const [message, setMessage] = useState('');

    // Domain management state (for seniors viewing own profile)
    const [seniorDomains, setSeniorDomains] = useState([]);
    const [domainsLoading, setDomainsLoading] = useState(false);
    const [newDomain, setNewDomain] = useState('');
    const [addingDomain, setAddingDomain] = useState(false);
    const [domainError, setDomainError] = useState('');

    // Fetch profile data
    useEffect(() => {
        if (!targetUserId) return;

        if (isOwnProfile) {
            // Own profile — use auth store
            if (!loggedInUser) hydrateProfile();
            else setViewedUser(loggedInUser);
        } else {
            // Another user's profile — fetch via API
            setLoadingProfile(true);
            getProfile(targetUserId)
                .then((data) => setViewedUser(data))
                .catch(() => setViewedUser(null))
                .finally(() => setLoadingProfile(false));
        }
    }, [targetUserId, isOwnProfile, loggedInUser, hydrateProfile]);

    // Sync own profile to viewedUser when it changes
    useEffect(() => {
        if (isOwnProfile && loggedInUser) setViewedUser(loggedInUser);
    }, [isOwnProfile, loggedInUser]);

    // Populate edit form
    useEffect(() => {
        if (isOwnProfile && viewedUser) {
            setProfileForm({
                name: viewedUser.name || '',
                current_level: viewedUser.current_level || '',
                availability: !!viewedUser.availability,
            });
        }
    }, [isOwnProfile, viewedUser]);

    // Fetch domains for senior own profile
    useEffect(() => {
        if (isOwnProfile && loggedInUser?.role === 'SENIOR' && loggedInUserId) {
            setDomainsLoading(true);
            getUserDomains(loggedInUserId)
                .then((data) => setSeniorDomains(Array.isArray(data) ? data : []))
                .catch(() => setSeniorDomains([]))
                .finally(() => setDomainsLoading(false));
        }
    }, [isOwnProfile, loggedInUser?.role, loggedInUserId]);

    const handleAddSeniorDomain = async (e) => {
        e.preventDefault();
        if (!newDomain.trim() || !loggedInUserId) return;
        setAddingDomain(true);
        setDomainError('');
        try {
            const result = await addDomain({ user_id: loggedInUserId, raw_interest_text: newDomain.trim() });
            setSeniorDomains((prev) =>
                prev.some((d) => d.domain_id === result.domain_id) ? prev : [...prev, result]
            );
            setNewDomain('');
        } catch (err) {
            const msg =
                err?.response?.data?.detail ||
                err?.response?.data?.error ||
                err?.message ||
                'Failed to add domain';
            setDomainError(msg);
        } finally {
            setAddingDomain(false);
        }
    };

    const handleProfileUpdate = async (event) => {
        event.preventDefault();
        if (!loggedInUserId) return;
        await updateProfile(loggedInUserId, profileForm);
        await hydrateProfile();
        setMessage('Profile updated.');
    };

    const handleAddAchievement = async (event) => {
        event.preventDefault();
        if (!loggedInUserId) return;
        await addAchievement(loggedInUserId, achievementForm);
        await hydrateProfile();
        setAchievementForm({ title: '', proof_url: '' });
        setMessage('Achievement added.');
    };

    if (!targetUserId) {
        return (
            <EffectsLayout title="Profile 👤" tagline="Please login first.">
                <p style={{ color: '#666' }}>Please login to view your profile.</p>
            </EffectsLayout>
        );
    }

    const displayUser = viewedUser;
    const pageTitle = isOwnProfile ? 'Your Profile 👤' : `${displayUser?.name || 'User'}'s Profile`;
    const pageTagline = isOwnProfile ? 'Manage your account and achievements.' : 'Viewing mentor profile.';

    return (
        <EffectsLayout title={pageTitle} tagline={pageTagline}>
            {/* Profile Info */}
            {loadingProfile ? (
                <p style={{ color: '#666' }}>Loading profile...</p>
            ) : displayUser ? (
                <div className="fx-glass fx-reveal">
                    <h3 className="fx-section-title">{isOwnProfile ? 'Your Info' : 'Profile Info'}</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 24px' }}>
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Name</p>
                            <p style={{ color: '#f0f0f0', margin: 0 }}>{displayUser.name}</p>
                        </div>
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Role</p>
                            <span className="badge badge-role">{displayUser.role}</span>
                        </div>
                        {/* Trust score: only show to others viewing a senior's profile, not to the senior themselves */}
                        {!isOwnProfile && displayUser.role === 'SENIOR' && (
                            <div>
                                <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Trust Score</p>
                                <TrustScoreBadge score={displayUser.trust_score} />
                            </div>
                        )}
                        {isOwnProfile && (
                            <>
                                <div>
                                    <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Email</p>
                                    <p style={{ color: '#f0f0f0', margin: 0 }}>{displayUser.email}</p>
                                </div>
                                <div>
                                    <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Active Load</p>
                                    <p style={{ color: '#f0f0f0', margin: 0 }}>{displayUser.active_load}</p>
                                </div>
                            </>
                        )}
                        {!isOwnProfile && displayUser.current_level && (
                            <div>
                                <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Level</p>
                                <p style={{ color: '#f0f0f0', margin: 0 }}>{displayUser.current_level}</p>
                            </div>
                        )}
                    </div>

                    {/* Connect / Send Message button — student viewing a senior */}
                    {!isOwnProfile && displayUser.role === 'SENIOR' && loggedInUser?.role === 'STUDENT' && (
                        <div style={{ marginTop: 16 }}>
                            <button
                                className="btn-primary"
                                disabled={connectStatus === 'sent' || connectStatus === 'sending'}
                                onClick={async () => {
                                    setConnectStatus('sending');
                                    try {
                                        await sendMessageRequest({
                                            student_id: loggedInUserId,
                                            senior_id: targetUserId,
                                        });
                                        setConnectStatus('sent');
                                    } catch (err) {
                                        if (err?.response?.status === 409) {
                                            setConnectStatus('exists');
                                        } else {
                                            setConnectStatus('error');
                                        }
                                    }
                                }}
                                style={{ padding: '8px 24px', fontSize: 14 }}
                            >
                                {connectStatus === 'sending' ? 'Sending...' :
                                 connectStatus === 'sent' ? 'Request Sent ✓' :
                                 connectStatus === 'exists' ? 'Already Connected' :
                                 connectStatus === 'error' ? 'Failed — Retry' :
                                 '💬 Send Message Request'}
                            </button>
                            {connectStatus === 'sent' && (
                                <button
                                    className="btn-secondary"
                                    onClick={() => navigate('/messages')}
                                    style={{ marginLeft: 10, padding: '8px 20px', fontSize: 14 }}
                                >
                                    Go to Messages
                                </button>
                            )}
                            {connectStatus === 'exists' && (
                                <button
                                    className="btn-secondary"
                                    onClick={() => navigate('/messages')}
                                    style={{ marginLeft: 10, padding: '8px 20px', fontSize: 14 }}
                                >
                                    Open Messages
                                </button>
                            )}
                        </div>
                    )}
                </div>
            ) : (
                <p style={{ color: '#666' }}>Profile not found.</p>
            )}

            {/* Update Profile — own profile only */}
            {isOwnProfile && (
                <div className="fx-glass fx-reveal">
                    <form onSubmit={handleProfileUpdate}>
                        <h3 className="fx-section-title">Update Profile</h3>
                        <input
                            type="text" placeholder="Name" value={profileForm.name}
                            onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                            className="dark-input" style={{ marginBottom: 12 }}
                        />
                        <input
                            type="text" placeholder="Current level" value={profileForm.current_level}
                            onChange={(e) => setProfileForm({ ...profileForm, current_level: e.target.value })}
                            className="dark-input" style={{ marginBottom: 12 }}
                        />
                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, color: '#f0f0f0', fontSize: 14 }}>
                            <input
                                type="checkbox" checked={profileForm.availability}
                                onChange={(e) => setProfileForm({ ...profileForm, availability: e.target.checked })}
                                className="dark-checkbox"
                            />
                            Available for mentoring
                        </label>
                        <button type="submit" className="btn-primary">Save</button>
                    </form>
                </div>
            )}

            {/* Manage Domains — own profile, senior only */}
            {isOwnProfile && displayUser?.role === 'SENIOR' && (
                <div className="fx-glass fx-reveal">
                    <h3 className="fx-section-title">Your Expertise Domains</h3>
                    <p style={{ color: '#8a8a8a', fontSize: 13, marginBottom: 12 }}>
                        Add domains you have expertise in so juniors can find and match with you.
                    </p>
                    {domainsLoading ? (
                        <p style={{ color: '#666' }}>Loading domains...</p>
                    ) : seniorDomains.length === 0 ? (
                        <p style={{ color: '#999', fontSize: 14 }}>No domains added yet. Add your expertise below!</p>
                    ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                            {seniorDomains.map((d) => (
                                <DomainBadge key={d.domain_id} domain={d} />
                            ))}
                        </div>
                    )}
                    <form onSubmit={handleAddSeniorDomain} style={{ display: 'flex', gap: 8 }}>
                        <input
                            type="text"
                            placeholder="Add a domain (e.g. Machine Learning)"
                            value={newDomain}
                            onChange={(e) => setNewDomain(e.target.value)}
                            className="dark-input"
                            style={{ flex: 1 }}
                        />
                        <button
                            type="submit"
                            disabled={addingDomain || !newDomain.trim()}
                            className="btn-primary"
                            style={{ opacity: addingDomain || !newDomain.trim() ? 0.5 : 1 }}
                        >
                            {addingDomain ? 'Adding...' : '+ Add'}
                        </button>
                    </form>
                    {domainError && (
                        <p style={{ color: '#ef4444', fontSize: 13, marginTop: 6, marginBottom: 0 }}>
                            {domainError}
                        </p>
                    )}
                </div>
            )}

            {/* Add Achievement — own profile, senior only */}
            {isOwnProfile && displayUser?.role === 'SENIOR' && (
                <div className="fx-glass fx-reveal">
                    <form onSubmit={handleAddAchievement}>
                        <h3 className="fx-section-title">Add Achievement</h3>
                        <input
                            type="text" placeholder="Title" value={achievementForm.title}
                            onChange={(e) => setAchievementForm({ ...achievementForm, title: e.target.value })}
                            className="dark-input" style={{ marginBottom: 12 }} required
                        />
                        <input
                            type="url" placeholder="Proof URL" value={achievementForm.proof_url}
                            onChange={(e) => setAchievementForm({ ...achievementForm, proof_url: e.target.value })}
                            className="dark-input" style={{ marginBottom: 12 }}
                        />
                        <button type="submit" className="btn-primary">Add Achievement</button>
                    </form>
                </div>
            )}

            {/* Achievements list */}
            <div className="fx-glass fx-reveal">
                <h3 className="fx-section-title">Achievements</h3>
                {(displayUser?.achievements || []).length === 0 ? (
                    <p style={{ color: '#666', fontSize: 14 }}>No achievements yet.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {(displayUser?.achievements || []).map((a) => (
                            <div key={a.id} style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                padding: '10px 14px', background: 'rgba(255,255,255,0.04)',
                                borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)',
                            }}>
                                <span style={{ color: '#f0f0f0', fontSize: 14 }}>{a.title}</span>
                                <span className={`badge ${a.verified ? 'badge-resolved' : 'badge-pending'}`}>
                                    {a.verified ? '✓ Verified' : 'Pending'}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {message && <p className="msg-success" style={{ marginTop: 16 }}>{message}</p>}
        </EffectsLayout>
    );
}
