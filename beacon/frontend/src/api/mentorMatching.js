/**
 * Calls Module 2 mentor matching endpoints.
 */
import axiosInstance from './axiosInstance';

export const findMentors = async (payload) => {
    const response = await axiosInstance.post('/api/mentor-matching/find/', payload);
    return response.data;
};

export const connectMentor = async (payload) => {
    const response = await axiosInstance.post('/api/mentor-matching/connect/', payload);
    return response.data;
};

export const findPeers = async (payload) => {
    const response = await axiosInstance.post('/api/peer-matching/find/', payload);
    return response.data;
};
