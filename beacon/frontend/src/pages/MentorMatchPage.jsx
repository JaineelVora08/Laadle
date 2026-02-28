import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { getUserDomains, addDomain } from '../api/domains';
import { findMentors } from '../api/mentorMatching';
import DomainBadge from '../components/DomainBadge';
import MentorCard from '../components/MentorCard';
import EffectsLayout from '../components/EffectsLayout';

export default function MentorMatchPage() {
    const userId = useAuthStore((s) => s.userId);
    const [userDomains, setUserDomains] = useState([]);
    const [selectedDomain, setSelectedDomain] = useState(null);
    const [mentors, setMentors] = useState([]);
    const [loading, setLoading] = useState(false);
    const [domainsLoading, setDomainsLoading] = useState(true);
    const [newDomain, setNewDomain] = useState('');
    const [addingDomain, setAddingDomain] = useState(false);
    const [addError, setAddError] = useState('');

    useEffect(() => {
        if (!userId) return;
        setDomainsLoading(true);
        getUserDomains(userId)
            .then((data) => setUserDomains(Array.isArray(data) ? data : []))
            .catch(() => { })
            .finally(() => setDomainsLoading(false));
    }, [userId]);

    const handleSelectDomain = async (domain) => {
        setSelectedDomain(domain);
        setLoading(true);
        setMentors([]);
        try {
            const result = await findMentors({ student_id: userId, domain_id: domain.domain_id, priority: 1 });
            setMentors(Array.isArray(result) ? result : (result?.matched_seniors || []));
        } catch { setMentors([]); }
        finally { setLoading(false); }
    };

    const handleAddDomain = async (e) => {
        e.preventDefault();
        if (!newDomain.trim() || !userId) return;
        setAddingDomain(true);
        setAddError('');
        try {
            const result = await addDomain({ user_id: userId, raw_interest_text: newDomain.trim() });
            setUserDomains((prev) => [...prev, result]);
            setNewDomain('');
        } catch (err) {
            const msg =
                err?.response?.data?.detail ||
                err?.response?.data?.error ||
                err?.message ||
                'Failed to add domain';
            console.error('Add domain error:', err?.response?.status, err?.response?.data || err);
            setAddError(msg);
        } finally {
            setAddingDomain(false);
        }
    };

    return (
        <EffectsLayout
            title="Find a Mentor 🎯"
            tagline="Select a domain to find mentors for."
        >
            {/* Domain selector */}
            <div className="fx-glass fx-reveal">
                <h3 className="fx-section-title">Your Domains</h3>
                {domainsLoading ? (
                    <p style={{ color: '#666' }}>Loading your domains...</p>
                ) : userDomains.length === 0 ? (
                    <p style={{ color: '#666' }}>No domains yet. Add one below!</p>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {userDomains.map((d) => (
                            <DomainBadge key={d.domain_id} domain={d} onClick={() => handleSelectDomain(d)} />
                        ))}
                    </div>
                )}
                {/* Add domain form */}
                <form onSubmit={handleAddDomain} style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                    <input
                        type="text"
                        placeholder="Add a domain (e.g. Machine Learning)"
                        value={newDomain}
                        onChange={(e) => setNewDomain(e.target.value)}
                        style={{
                            flex: 1,
                            padding: '8px 14px',
                            borderRadius: 8,
                            border: '1px solid rgba(255,255,255,0.12)',
                            background: 'rgba(255,255,255,0.06)',
                            color: 'var(--text-primary, #fff)',
                            fontSize: 14,
                            outline: 'none',
                        }}
                    />
                    <button
                        type="submit"
                        disabled={addingDomain || !newDomain.trim()}
                        style={{
                            padding: '8px 18px',
                            borderRadius: 8,
                            border: 'none',
                            background: addingDomain || !newDomain.trim() ? 'rgba(255,255,255,0.08)' : 'var(--accent, #00b4d8)',
                            color: '#fff',
                            fontWeight: 600,
                            fontSize: 14,
                            cursor: addingDomain || !newDomain.trim() ? 'default' : 'pointer',
                            opacity: addingDomain || !newDomain.trim() ? 0.5 : 1,
                            transition: 'all 0.2s ease',
                        }}
                    >
                        {addingDomain ? 'Adding...' : '+ Add'}
                    </button>
                </form>
                {addError && (
                    <p style={{ color: '#ef4444', fontSize: 13, marginTop: 6, marginBottom: 0 }}>
                        {addError}
                    </p>
                )}
            </div>

            {/* Mentor list */}
            {selectedDomain && (
                <div className="fx-reveal">
                    <h3 className="fx-section-title">
                        Mentors for "{selectedDomain.name || selectedDomain.domain_name}"
                    </h3>
                    {loading ? (
                        <p style={{ color: '#666' }}>Searching for mentors...</p>
                    ) : mentors.length === 0 ? (
                        <div className="fx-glass" style={{ textAlign: 'center' }}>
                            <p style={{ margin: 0, color: '#999' }}>
                                No mentors found for this domain yet. We'll notify available seniors.
                            </p>
                        </div>
                    ) : (
                        mentors.map((m) => (
                            <MentorCard key={m.senior_id} mentor={m} domainId={selectedDomain.domain_id} />
                        ))
                    )}
                </div>
            )}
        </EffectsLayout>
    );
}
