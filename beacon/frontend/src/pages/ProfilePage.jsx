import React from 'react';
import { useEffect, useState } from 'react';
import { addAchievement, updateProfile } from '../api/profile';
import { useAuthStore } from '../store/authStore';

/**
 * ProfilePage — shows UserProfileResponse, achievement list
 */
export default function ProfilePage() {
    const user = useAuthStore((state) => state.user);
    const userId = useAuthStore((state) => state.userId);
    const hydrateProfile = useAuthStore((state) => state.hydrateProfile);

    const [profileForm, setProfileForm] = useState({ name: '', current_level: '', availability: true });
    const [achievementForm, setAchievementForm] = useState({ title: '', proof_url: '' });
    const [message, setMessage] = useState('');

    useEffect(() => {
        if (!user && userId) {
            hydrateProfile();
        }
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
        return <div style={{ maxWidth: 680, margin: '2rem auto' }}>Please login first.</div>;
    }

    return (
        <div style={{ maxWidth: 680, margin: '2rem auto' }}>
            <h2>Profile</h2>
            {user ? (
                <div style={{ marginBottom: 16 }}>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Role:</strong> {user.role}</p>
                    <p><strong>Trust Score:</strong> {user.trust_score}</p>
                    <p><strong>Active Load:</strong> {user.active_load}</p>
                </div>
            ) : (
                <p>Loading profile...</p>
            )}

            <form onSubmit={handleProfileUpdate} style={{ marginBottom: 20 }}>
                <h3>Update Profile</h3>
                <input
                    type="text"
                    placeholder="Name"
                    value={profileForm.name}
                    onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                />
                <input
                    type="text"
                    placeholder="Current level"
                    value={profileForm.current_level}
                    onChange={(e) => setProfileForm({ ...profileForm, current_level: e.target.value })}
                    style={{ display: 'block', width: '100%', marginBottom: 12 }}
                />
                <label style={{ display: 'block', marginBottom: 12 }}>
                    <input
                        type="checkbox"
                        checked={profileForm.availability}
                        onChange={(e) => setProfileForm({ ...profileForm, availability: e.target.checked })}
                    /> Availability
                </label>
                <button type="submit">Save</button>
            </form>

            {user?.role === 'SENIOR' ? (
                <form onSubmit={handleAddAchievement}>
                    <h3>Add Achievement</h3>
                    <input
                        type="text"
                        placeholder="Title"
                        value={achievementForm.title}
                        onChange={(e) => setAchievementForm({ ...achievementForm, title: e.target.value })}
                        style={{ display: 'block', width: '100%', marginBottom: 12 }}
                        required
                    />
                    <input
                        type="url"
                        placeholder="Proof URL"
                        value={achievementForm.proof_url}
                        onChange={(e) => setAchievementForm({ ...achievementForm, proof_url: e.target.value })}
                        style={{ display: 'block', width: '100%', marginBottom: 12 }}
                    />
                    <button type="submit">Add Achievement</button>
                </form>
            ) : null}

            <h3 style={{ marginTop: 20 }}>Achievements</h3>
            <ul>
                {(user?.achievements || []).map((achievement) => (
                    <li key={achievement.id}>{achievement.title} {achievement.verified ? '(Verified)' : '(Pending)'}</li>
                ))}
            </ul>

            {message ? <p>{message}</p> : null}
        </div>
    );
}
