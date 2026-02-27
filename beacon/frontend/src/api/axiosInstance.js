/**
 * Base axios instance.
 * - baseURL: process.env.REACT_APP_API_BASE_URL
 * - Attaches Authorization: Bearer <token> from authStore on every request
 * - Auto-refreshes token on 401 using POST /api/auth/token/refresh/
 */
const axiosInstance = null; // TODO: implement
export default axiosInstance;
