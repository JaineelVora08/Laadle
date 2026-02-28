/**
 * Calls Module 1 messaging endpoints.
 */
import axiosInstance from './axiosInstance';

export const sendMessageRequest = async (payload) => {
    const response = await axiosInstance.post('/api/messages/request/', payload);
    return response.data;
};

export const getSeniorPendingRequests = async (seniorId) => {
    const response = await axiosInstance.get(`/api/messages/requests/senior/${seniorId}/`);
    return response.data;
};

export const acceptRequest = async (requestId) => {
    const response = await axiosInstance.post(`/api/messages/request/${requestId}/accept/`);
    return response.data;
};

export const rejectRequest = async (requestId) => {
    const response = await axiosInstance.post(`/api/messages/request/${requestId}/reject/`);
    return response.data;
};

export const sendMessage = async (threadId, payload) => {
    const response = await axiosInstance.post(`/api/messages/thread/${threadId}/send/`, payload);
    return response.data;
};

export const getThread = async (threadId) => {
    const response = await axiosInstance.get(`/api/messages/thread/${threadId}/`);
    return response.data;
};

export const getUserThreads = async (userId) => {
    const response = await axiosInstance.get(`/api/messages/threads/${userId}/`);
    return response.data;
};
