/**
 * Calls Module 1 auth endpoints.
 */
import axios from 'axios';
import axiosInstance from './axiosInstance';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const register = async (payload) => {
	const response = await axiosInstance.post('/api/auth/register/', payload);
	return response.data;
};

export const login = async (payload) => {
	const response = await axiosInstance.post('/api/auth/login/', payload);
	return response.data;
};

export const googleLogin = async (payload) => {
	const response = await axiosInstance.post('/api/auth/google/login/', payload);
	return response.data;
};

export const logout = async (refreshToken) => {
	const response = await axiosInstance.post('/api/auth/logout/', { refresh: refreshToken });
	return response.data;
};

export const refresh = async (token) => {
	const response = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, { refresh: token });
	return response.data;
};
