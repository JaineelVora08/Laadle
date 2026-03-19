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

/**
 * Student submits a follow-up question on an existing query.
 * Returns: { answer, source, confidence?, disclaimer?, message? }
 */
export const submitFollowUp = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/followup/`, payload);
    return response.data;
};

/**
 * Student rates the resolved advice (1-5 stars).
 * Payload: { student_id, rating }
 */
export const rateQuery = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/rate/`, payload);
    return response.data;
};

/**
 * Student reports whether the advice helped (follow-through).
 * Payload: { student_id, success: bool, proof_url?: string }
 */
export const submitFollowThrough = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/follow-through/`, payload);
    return response.data;
};

/**
 * Student triggers early finalization using majority of responses received so far.
 * Payload: { student_id }
 */
export const finalizeQuery = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/finalize/`, payload);
    return response.data;
};

/**
 * Get response status (counts, deadline, finalization eligibility).
 */
export const getQueryResponseStatus = async (queryId) => {
    const response = await axiosInstance.get(`/api/query/${queryId}/response-status/`);
    return response.data;
};
