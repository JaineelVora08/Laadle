/**
 * Calls Module 1 user profile endpoints.
 */
export const getProfile = async (userId) => { /* GET /api/profile/<userId>/ */ };
export const updateProfile = async (userId, payload) => { /* PUT /api/profile/<userId>/update/ */ };
export const addAchievement = async (userId, payload) => { /* POST /api/profile/<userId>/achievements/ */ };
export const getAchievements = async (userId) => { /* GET /api/profile/<userId>/achievements/ */ };
