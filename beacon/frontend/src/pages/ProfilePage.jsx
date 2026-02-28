import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getProfile, addAchievement, updateProfile } from '../api/profile';
import { useAuthStore } from '../store/authStore';
import EffectsLayout from '../components/EffectsLayout';
import TrustScoreBadge from '../components/TrustScoreBadge';

export default function ProfilePage() {
    const { userId: paramUserId } = useParams();
    const loggedInUserId = useAuthStore((state) => state.userId);
    const loggedInUser = useAuthStore((state) => state.user);
    const hydrateProfile = useAuthStore((state) => state.hydrateProfile);

    // Determine whose profile we're viewing
    const targetUserId = paramUserId || loggedInUserId;
    const isOwnProfile = !paramUserId || paramUserId === loggedInUserId;

    const [viewedUser, setViewedUser] = useState(null);
    const [loadingProfile, setLoadingProfile] = useState(false);

    const [profileForm, setProfileForm] = useState({ name: '', current_level: '', availability: true });
    const [achievementForm, setAchievementForm] = useState({ title: '', proof_url: '' });
    const [message, setMessage] = useState('');

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
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Trust Score</p>
                            <TrustScoreBadge score={displayUser.trust_score} />
                        </div>
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
