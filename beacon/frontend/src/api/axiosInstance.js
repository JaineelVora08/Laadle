/**
 * Base axios instance.
 * - baseURL: process.env.REACT_APP_API_BASE_URL
 * - Attaches Authorization: Bearer <token> from authStore on every request
 * - Auto-refreshes token on 401 using POST /api/auth/token/refresh/
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const ACCESS_TOKEN_KEY = 'beacon_access_token';
const REFRESH_TOKEN_KEY = 'beacon_refresh_token';

const axiosInstance = axios.create({
	baseURL: API_BASE_URL,
});

axiosInstance.interceptors.request.use((config) => {
	const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
	if (accessToken) {
		config.headers = config.headers || {};
		config.headers.Authorization = `Bearer ${accessToken}`;
	}
	return config;
});

let isRefreshing = false;
let queuedRequests = [];

const resolveQueue = (token) => {
	queuedRequests.forEach((callback) => callback(token));
	queuedRequests = [];
};

axiosInstance.interceptors.response.use(
	(response) => response,
	async (error) => {
		const originalRequest = error.config;
		if (!error.response || error.response.status !== 401 || originalRequest._retry) {
			return Promise.reject(error);
		}

		const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
		if (!refreshToken) {
			return Promise.reject(error);
		}

		if (isRefreshing) {
			return new Promise((resolve) => {
				queuedRequests.push((token) => {
					originalRequest.headers.Authorization = `Bearer ${token}`;
					resolve(axiosInstance(originalRequest));
				});
			});
		}

		originalRequest._retry = true;
		isRefreshing = true;

		try {
			const refreshResponse = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
				refresh: refreshToken,
			});

			const { access, refresh } = refreshResponse.data;
			localStorage.setItem(ACCESS_TOKEN_KEY, access);
			if (refresh) {
				localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
			}

			resolveQueue(access);
			originalRequest.headers.Authorization = `Bearer ${access}`;
			return axiosInstance(originalRequest);
		} catch (refreshError) {
			localStorage.removeItem(ACCESS_TOKEN_KEY);
			localStorage.removeItem(REFRESH_TOKEN_KEY);
			return Promise.reject(refreshError);
		} finally {
			isRefreshing = false;
		}
	}
);

export default axiosInstance;
