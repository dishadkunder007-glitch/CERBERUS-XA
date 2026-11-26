import axios from 'axios';

// Base API configuration for FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45 seconds for multimodal AI inference operations
  headers: {
    'Accept': 'application/json',
  },
});

// Interceptor for logging & debugging during hackathon development
apiClient.interceptors.request.use(
  (config) => {
    // Helpful log for debugging network requests in browser console
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorDetails = {
      status: error.response?.status,
      message: error.response?.data?.detail || error.response?.data?.message || error.message,
      url: error.config?.url,
      code: error.code
    };
    if (import.meta.env.DEV) {
      console.warn(`[API Error]`, errorDetails);
    }
    return Promise.reject(errorDetails);
  }
);

export default apiClient;
