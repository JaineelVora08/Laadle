import React, { useEffect, useState } from 'react';
import { addAchievement, updateProfile } from '../api/profile';
import { useAuthStore } from '../store/authStore';
import EffectsLayout from '../components/EffectsLayout';

export default function ProfilePage() {
    const user = useAuthStore((state) => state.user);
    const userId = useAuthStore((state) => state.userId);
    const hydrateProfile = useAuthStore((state) => state.hydrateProfile);

    const [profileForm, setProfileForm] = useState({ name: '', current_level: '', availability: true });
    const [achievementForm, setAchievementForm] = useState({ title: '', proof_url: '' });
    const [message, setMessage] = useState('');

    useEffect(() => {
        if (!user && userId) hydrateProfile();
    }, [user, userId, hydrateProfile]);

    useEffect(() => {
        if (user) {
            setProfileForm({
                name: user.name || '',
                current_level: user.current_level || '',
                availability: !!user.availability,
            });
        }
    }, [user]);

    const handleProfileUpdate = async (event) => {
        event.preventDefault();
        if (!userId) return;
        await updateProfile(userId, profileForm);
        await hydrateProfile();
        setMessage('Profile updated.');
    };

    const handleAddAchievement = async (event) => {
        event.preventDefault();
        if (!userId) return;
        await addAchievement(userId, achievementForm);
        await hydrateProfile();
        setAchievementForm({ title: '', proof_url: '' });
        setMessage('Achievement added.');
    };

    if (!userId) {
        return (
            <EffectsLayout title="Profile 👤" tagline="Please login first.">
                <p style={{ color: '#666' }}>Please login to view your profile.</p>
            </EffectsLayout>
        );
    }

    return (
        <EffectsLayout title="Profile 👤" tagline="Manage your account and achievements.">
            {/* Profile Info */}
            {user ? (
                <div className="fx-glass fx-reveal">
                    <h3 className="fx-section-title">Your Info</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 24px' }}>
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Email</p>
                            <p style={{ color: '#f0f0f0', margin: 0 }}>{user.email}</p>
                        </div>
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Role</p>
                            <span className="badge badge-role">{user.role}</span>
                        </div>
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Trust Score</p>
                            <p style={{ color: '#00b4d8', fontWeight: 600, margin: 0 }}>{user.trust_score}</p>
                        </div>
                        <div>
                            <p style={{ color: '#666', fontSize: 12, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 1 }}>Active Load</p>
                            <p style={{ color: '#f0f0f0', margin: 0 }}>{user.active_load}</p>
                        </div>
                    </div>
                </div>
            ) : (
                <p style={{ color: '#666' }}>Loading profile...</p>
            )}

            {/* Update Profile */}
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

            {/* Add Achievement (senior only) */}
            {user?.role === 'SENIOR' && (
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
                {(user?.achievements || []).length === 0 ? (
                    <p style={{ color: '#666', fontSize: 14 }}>No achievements yet.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {(user?.achievements || []).map((a) => (
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
