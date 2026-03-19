/**
 * Calls Module 1 messaging endpoints.
 * Optimized: single-fetch cache, no redundant requests.
 */
import axiosInstance from './axiosInstance';

// ──── Cached requests fetch ────
let _cachedRequests = null;
let _cacheTimestamp = 0;
const CACHE_TTL = 30_000; // 30 seconds

async function fetchAllRequests(forceRefresh = false) {
    const now = Date.now();
    if (!forceRefresh && _cachedRequests && now - _cacheTimestamp < CACHE_TTL) {
        return _cachedRequests;
    }
    const response = await axiosInstance.get('/api/dm/requests/');
    _cachedRequests = Array.isArray(response.data) ? response.data : [];
    _cacheTimestamp = Date.now();
    return _cachedRequests;
}

/** Invalidate cache (e.g. after accept/reject/initiate) */
function invalidateCache() {
    _cachedRequests = null;
    _cacheTimestamp = 0;
}

// ──── Public API ────

export const sendMessageRequest = async (payload) => {
    invalidateCache();
    const response = await axiosInstance.post('/api/dm/initiate/', {
        student_id: payload.student_id,
        senior_id: payload.senior_id,
        ...(payload.query_id ? { query_id: payload.query_id } : {}),
        ...(payload.domain_name ? { domain_name: payload.domain_name } : {}),
    });
    return response.data;
};

export const getSeniorPendingRequests = async (seniorId) => {
    const all = await fetchAllRequests();
    return all
        .filter((r) => r.status === 'PENDING' && String(r.senior_id) === String(seniorId))
        .map((r) => ({ ...r, preview_text: r.intro_message || '' }));
};

export const acceptRequest = async (requestId) => {
    invalidateCache();
    const response = await axiosInstance.post(`/api/dm/requests/${requestId}/respond/`, {
        action: 'ACCEPT',
    });
    const request = response.data || {};
    return {
        ...request,
        thread_id: String(request.id),
    };
};

export const rejectRequest = async (requestId) => {
    invalidateCache();
    const response = await axiosInstance.post(`/api/dm/requests/${requestId}/respond/`, {
        action: 'REJECT',
    });
    return response.data;
};

export const sendMessage = async (threadId, payload) => {
    const response = await axiosInstance.post(`/api/dm/requests/${threadId}/messages/`, payload);
    const msg = response.data || {};
    return {
        ...msg,
        timestamp: msg.sent_at,
    };
};

/**
 * getThread — only fetches messages now. Uses cached request data
 * instead of re-fetching all requests.
 */
export const getThread = async (threadId) => {
    const [allRequests, messagesRes] = await Promise.all([
        fetchAllRequests(),
        axiosInstance.get(`/api/dm/requests/${threadId}/messages/`),
    ]);
    const request = allRequests.find((r) => String(r.id) === String(threadId));
    const messages = Array.isArray(messagesRes.data)
        ? messagesRes.data.map((m) => ({ ...m, timestamp: m.sent_at }))
        : [];

    return {
        thread_id: String(threadId),
        request,
        messages,
    };
};

export const getUserThreads = async (userId) => {
    const all = await fetchAllRequests();

    return all
        .filter((r) => r.status === 'ACCEPTED')
        .map((r) => {
            const isStudent = String(r.student_id) === String(userId);
            const otherName = isStudent ? r.senior_name : r.student_name;
            return {
                thread_id: String(r.id),
                other_user_name: otherName,
                last_message: r.intro_message || '',
                last_timestamp: r.responded_at || r.created_at,
                unread_count: 0,
            };
        });
};

/**
 * Combined fetch for page load — fetches requests once,
 * returns both threads and pending requests.
 */
export const getThreadsAndPending = async (userId, role) => {
    const all = await fetchAllRequests(true); // force refresh on page load

    const threads = all
        .filter((r) => r.status === 'ACCEPTED')
        .map((r) => {
            const isStudent = String(r.student_id) === String(userId);
            const otherName = isStudent ? r.senior_name : r.student_name;
            return {
                thread_id: String(r.id),
                other_user_name: otherName,
                last_message: r.intro_message || '',
                last_timestamp: r.responded_at || r.created_at,
                unread_count: 0,
            };
        });

    let pendingRequests = [];
    if (role === 'SENIOR') {
        pendingRequests = all
            .filter((r) => r.status === 'PENDING' && String(r.senior_id) === String(userId))
            .map((r) => ({ ...r, preview_text: r.intro_message || '' }));
    }

    // Student's sent requests (PENDING ones they're waiting on)
    let sentRequests = [];
    if (role === 'STUDENT') {
        sentRequests = all
            .filter((r) => r.status === 'PENDING' && String(r.student_id) === String(userId))
            .map((r) => ({
                ...r,
                other_user_name: r.senior_name,
                preview_text: r.intro_message || '',
            }));
    }

    return { threads, pendingRequests, sentRequests };
};
