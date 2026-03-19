/**
 * Calls Module 1 user profile endpoints.
 */
import axiosInstance from './axiosInstance';

export const getProfile = async (userId) => {
	const response = await axiosInstance.get(`/api/profile/${userId}/`);
	return response.data;
};

export const updateProfile = async (userId, payload) => {
	const response = await axiosInstance.patch(`/api/profile/${userId}/update/`, payload);
	return response.data;
};

export const addAchievement = async (userId, payload) => {
	const response = await axiosInstance.post(`/api/profile/${userId}/achievements/`, payload);
	return response.data;
};

export const getAchievements = async (userId) => {
	const response = await axiosInstance.get(`/api/profile/${userId}/achievements/`);
	return response.data;
};

export const completeSeniorOnboarding = async (userId, payload) => {
	const response = await axiosInstance.post(`/api/profile/${userId}/onboarding/`, payload);
	return response.data;
};
