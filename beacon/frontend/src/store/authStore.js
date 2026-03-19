/**
 * Zustand store for auth state.
 * State: { user: UserProfileResponse | null, token: string | null }
 * Actions: login(credentials), logout(), setUser(user)
 */
import { create } from 'zustand';
import { googleLogin, login as loginApi, logout as logoutApi, register as registerApi } from '../api/auth';
import { getProfile } from '../api/profile';

const ACCESS_TOKEN_KEY = 'beacon_access_token';
const REFRESH_TOKEN_KEY = 'beacon_refresh_token';
const USER_ID_KEY = 'beacon_user_id';
const ROLE_KEY = 'beacon_role';
const PROFILE_COMPLETED_KEY = 'beacon_profile_completed';

const saveSession = ({ access, refresh, user_id, role, profile_completed }) => {
	localStorage.setItem(ACCESS_TOKEN_KEY, access);
	localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
	localStorage.setItem(USER_ID_KEY, user_id);
	localStorage.setItem(ROLE_KEY, role);
	localStorage.setItem(PROFILE_COMPLETED_KEY, String(profile_completed ?? false));
};

const clearSession = () => {
	localStorage.removeItem(ACCESS_TOKEN_KEY);
	localStorage.removeItem(REFRESH_TOKEN_KEY);
	localStorage.removeItem(USER_ID_KEY);
	localStorage.removeItem(ROLE_KEY);
	localStorage.removeItem(PROFILE_COMPLETED_KEY);
};

export const useAuthStore = create((set, get) => ({
	user: null,
	token: localStorage.getItem(ACCESS_TOKEN_KEY),
	refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
	userId: localStorage.getItem(USER_ID_KEY),
	role: localStorage.getItem(ROLE_KEY),
	profileCompleted: localStorage.getItem(PROFILE_COMPLETED_KEY) === 'true',

	setUser: (user) => set({ user }),

	hydrateProfile: async () => {
		const userId = get().userId;
		if (!userId) return null;
		const profile = await getProfile(userId);
		set({ user: profile, role: profile.role, profileCompleted: profile.profile_completed ?? false });
		localStorage.setItem(PROFILE_COMPLETED_KEY, String(profile.profile_completed ?? false));
		return profile;
	},

	login: async (credentials) => {
		const data = await loginApi(credentials);
		saveSession(data);
		set({ token: data.access, refreshToken: data.refresh, userId: data.user_id, role: data.role, profileCompleted: data.profile_completed ?? false });
		await get().hydrateProfile();
		return data;
	},

	register: async (payload) => {
		const data = await registerApi(payload);
		saveSession(data);
		set({ token: data.access, refreshToken: data.refresh, userId: data.user_id, role: data.role, profileCompleted: data.profile_completed ?? false });
		await get().hydrateProfile();
		return data;
	},

	googleLogin: async (payload) => {
		const data = await googleLogin(payload);
		saveSession(data);
		set({ token: data.access, refreshToken: data.refresh, userId: data.user_id, role: data.role, profileCompleted: data.profile_completed ?? false });
		await get().hydrateProfile();
		return data;
	},

	logout: async () => {
		const refreshToken = get().refreshToken;
		if (refreshToken) {
			try {
				await logoutApi(refreshToken);
			} catch (error) {
			}
		}
		clearSession();
		set({ user: null, token: null, refreshToken: null, userId: null, role: null, profileCompleted: false });
	},
}));
