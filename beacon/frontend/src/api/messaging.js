/**
 * Calls Module 1 messaging endpoints.
 */
import axiosInstance from './axiosInstance';

export const sendMessageRequest = async (payload) => {
    const response = await axiosInstance.post('/api/dm/initiate/', {
        student_id: payload.student_id,
        senior_id: payload.senior_id,
        ...(payload.query_id ? { query_id: payload.query_id } : {}),
    });
    return response.data;
};

export const getSeniorPendingRequests = async (seniorId) => {
    const response = await axiosInstance.get('/api/dm/requests/');
    const all = Array.isArray(response.data) ? response.data : [];
    return all
        .filter((r) => r.status === 'PENDING' && String(r.senior_id) === String(seniorId))
        .map((r) => ({ ...r, preview_text: r.intro_message || '' }));
};

export const acceptRequest = async (requestId) => {
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

export const getThread = async (threadId) => {
    const [requestsRes, messagesRes] = await Promise.all([
        axiosInstance.get('/api/dm/requests/'),
        axiosInstance.get(`/api/dm/requests/${threadId}/messages/`),
    ]);
    const requests = Array.isArray(requestsRes.data) ? requestsRes.data : [];
    const request = requests.find((r) => String(r.id) === String(threadId));
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
    const response = await axiosInstance.get('/api/dm/requests/');
    const all = Array.isArray(response.data) ? response.data : [];

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
