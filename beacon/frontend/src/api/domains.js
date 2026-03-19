/**
 * Calls Module 2 domain management endpoints.
 */
import axiosInstance from './axiosInstance';

export const addDomain = async (payload) => {
    const response = await axiosInstance.post('/api/domains/add/', payload);
    return response.data;
};

export const getUserDomains = async (userId) => {
    const response = await axiosInstance.get(`/api/domains/user/${userId}/`);
    return response.data;
};

export const getAllDomains = async () => {
    const response = await axiosInstance.get('/api/domains/all/');
    return response.data;
};
