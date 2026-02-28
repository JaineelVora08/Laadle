import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { getUserDomains } from '../api/domains';
import { findMentors } from '../api/mentorMatching';
import DomainBadge from '../components/DomainBadge';
import MentorCard from '../components/MentorCard';

/**
 * MentorMatchPage — select domain then find and connect with mentors.
 */
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
            const result = await findMentors({
                student_id: userId,
                domain_id: domain.domain_id,
                priority: 'trust_score',
            });
            setMentors(result?.matched_seniors || []);
        } catch {
            setMentors([]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 800, margin: '2rem auto', padding: '0 16px' }}>
            <h2>Find a Mentor 🎯</h2>
            <p style={{ color: '#6b7280' }}>Select a domain to find mentors for.</p>

            {/* Domain selector */}
            {domainsLoading ? (
                <p style={{ color: '#9ca3af' }}>Loading your domains...</p>
            ) : userDomains.length === 0 ? (
                <p style={{ color: '#9ca3af' }}>
                    You have no domains yet. Add some from your dashboard first.
                </p>
            ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 24 }}>
                    {userDomains.map((d) => (
                        <DomainBadge
                            key={d.domain_id}
                            domain={{
                                ...d,
                                type: selectedDomain?.domain_id === d.domain_id ? d.type : d.type,
                            }}
                            onClick={() => handleSelectDomain(d)}
                        />
                    ))}
                </div>
            )}

            {/* Mentor list */}
            {selectedDomain && (
                <div>
                    <h3 style={{ marginBottom: 12 }}>
                        Mentors for "{selectedDomain.domain_name}"
                    </h3>
                    {loading ? (
                        <p style={{ color: '#9ca3af' }}>Searching for mentors...</p>
                    ) : mentors.length === 0 ? (
                        <div
                            style={{
                                padding: 20,
                                borderRadius: 12,
                                background: '#fefce8',
                                border: '1px solid #fde68a',
                                textAlign: 'center',
                            }}
                        >
                            <p style={{ margin: 0, color: '#92400e' }}>
                                No mentors found for this domain yet. We'll notify available seniors.
                            </p>
                        </div>
                    ) : (
                        mentors.map((m) => (
                            <MentorCard
                                key={m.senior_id}
                                mentor={m}
                                domainId={selectedDomain.domain_id}
                            />
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
