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

export const submitSeniorResponse = async (queryId, payload) => {
    const response = await axiosInstance.post(`/api/query/${queryId}/senior-response/`, payload);
    return response.data;
};

export const getSeniorPendingQueries = async (seniorId) => {
    const response = await axiosInstance.get(`/api/query/pending/senior/${seniorId}/`);
    return response.data;
};
