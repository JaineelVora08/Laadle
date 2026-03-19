/**
 * Mock data for development.
 * Import from here until backend devs are ready, then swap to real API calls.
 */

export const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYTFiMmMzZDQtZTVmNi03ODkwLWFiY2QtZWYxMjM0NTY3ODkwIiwicm9sZSI6IlNUVURFTlQifQ.mock_signature';

export const MOCK_STUDENT = {
    user_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    name: 'Aarav Sharma',
    email: 'aarav@iitj.ac.in',
    role: 'STUDENT',
    current_level: 'B.Tech Year 2',
    trust_score: 0.72,
    availability: true,
    momentum_score: 0.65,
    active_load: 1,
    achievements: [],
};

export const MOCK_SENIOR = {
    user_id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
    name: 'Priya Patel',
    email: 'priya@iitj.ac.in',
    role: 'SENIOR',
    current_level: 'M.Tech Year 1',
    trust_score: 0.91,
    availability: true,
    consistency_score: 0.88,
    active_load: 3,
    achievements: [
        { id: 'ach-001', title: 'Dean\'s List 2024', proof_url: 'https://example.com/proof1', verified: true },
        { id: 'ach-002', title: 'Google Summer of Code', proof_url: 'https://example.com/proof2', verified: true },
    ],
};

export const MOCK_DOMAINS = [
    { domain_id: 'dom-001', domain_name: 'Machine Learning', is_new_domain: false, similarity_score: 0.95 },
    { domain_id: 'dom-002', domain_name: 'Web Development', is_new_domain: false, similarity_score: 0.88 },
    { domain_id: 'dom-003', domain_name: 'Competitive Programming', is_new_domain: true, similarity_score: 0.72 },
];

export const MOCK_MENTOR_LIST = [
    {
        senior_id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
        name: 'Priya Patel',
        trust_score: 0.91,
        experience_level: 'Advanced',
        years_of_involvement: 3,
        availability: true,
        active_load: 3,
    },
    {
        senior_id: 'c3d4e5f6-a7b8-9012-cdef-123456789012',
        name: 'Rohan Gupta',
        trust_score: 0.84,
        experience_level: 'Intermediate',
        years_of_involvement: 2,
        availability: true,
        active_load: 2,
    },
];

export const MOCK_QUERY_RESPONSE = {
    query_id: 'qry-001-uuid-mock',
    provisional_answer: 'Based on available resources, the most effective approach to learning ML fundamentals is to start with Andrew Ng\'s Stanford course, then practice with Kaggle competitions. Focus on linear regression and neural networks first before moving to advanced topics like transformers.',
    disclaimer: 'This is an AI-generated provisional answer. A senior mentor will review and provide expert guidance shortly.',
    predicted_followups: [
        'What specific math prerequisites do I need for ML?',
        'How long does it typically take to become competent in ML?',
        'Are there any IIT Jodhpur specific ML resources or labs?',
    ],
    matched_senior_ids: [
        'b2c3d4e5-f6a7-8901-bcde-f12345678901',
        'c3d4e5f6-a7b8-9012-cdef-123456789012',
    ],
    status: 'PENDING_SENIOR',
};

export const MOCK_FINAL_RESPONSE = {
    query_id: 'qry-001-uuid-mock',
    final_answer: 'I recommend starting with CS229 (Andrew Ng) alongside 3Blue1Brown\'s linear algebra series. At IIT Jodhpur, join the AI/ML club and look into Prof. Anand Mishra\'s research group. Build a portfolio with 2-3 Kaggle projects before applying for internships.',
    conflict_detected: false,
    conflict_details: null,
    contributing_seniors: [{ senior_id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901', weight: 0.87 }],
    is_resolved: true,
};

export const MOCK_PENDING_REQUESTS = [
    {
        id: 'req-001',
        student_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        student_name: 'Aarav Sharma',
        preview_text: 'Hi, I saw your profile and wanted to ask about ML research opportunities...',
        status: 'PENDING',
        created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
        id: 'req-002',
        student_id: 'd4e5f6a7-b8c9-0123-defa-234567890123',
        student_name: 'Sneha Reddy',
        preview_text: 'Could you guide me on preparing for GSoC?',
        status: 'PENDING',
        created_at: new Date(Date.now() - 7200000).toISOString(),
    },
];

export const MOCK_THREAD = {
    thread_id: 'thread-001',
    student_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    senior_id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
    messages: [
        {
            id: 'msg-001',
            sender_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            content: 'Hi Priya! I wanted to ask about ML research.',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            is_read: true,
        },
        {
            id: 'msg-002',
            sender_id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
            content: 'Hey Aarav! Happy to help. What specifically interests you?',
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            is_read: true,
        },
    ],
};
