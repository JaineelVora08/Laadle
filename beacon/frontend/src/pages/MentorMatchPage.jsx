import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { getUserDomains } from '../api/domains';
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
                    <p style={{ color: '#666' }}>You have no domains yet. Add some from your dashboard first.</p>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {userDomains.map((d) => (
                            <DomainBadge key={d.domain_id} domain={d} onClick={() => handleSelectDomain(d)} />
                        ))}
                    </div>
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
