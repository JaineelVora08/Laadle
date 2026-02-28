/**
 * Calls Module 3 query orchestrator endpoints.
 */
import axiosInstance from './axiosInstance';

export const submitQuery = async (payload) => {
    const response = await axiosInstance.post('/api/query/submit/', payload);
    return response.data;
};

export const getQueryStatus = async (queryId) => {
    const response = await axiosInstance.get(`/api/query/${queryId}/status/`);
    return response.data;
};

/**
 * Step 1: Senior submits main advice.
 * Returns: { query_id, status: 'AWAITING_FAQ', predicted_faqs: [...] }
 */
export const submitSeniorAdvice = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/senior-response/`, payload);
    return response.data;
};

/**
 * Step 2: Senior submits FAQ answers.
 * Returns: { query_id, final_answer, agreements, disagreements, conflict_detected, ... }
 */
export const submitSeniorFAQ = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/senior-faq/`, payload);
    return response.data;
};

/** Legacy alias — kept for compatibility */
export const submitSeniorResponse = submitSeniorAdvice;

export const getSeniorPendingQueries = async (seniorId) => {
    const response = await axiosInstance.get(`/api/query/pending/senior/${seniorId}/`);
    return response.data;
};

export const getStudentQueries = async (studentId) => {
    const response = await axiosInstance.get(`/api/query/student/${studentId}/`);
    return response.data;
};
