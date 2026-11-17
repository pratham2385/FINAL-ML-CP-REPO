import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Accept': 'application/json',
  },
});

// Response interceptor to normalize error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An unexpected network error occurred.';
    if (error.response) {
      const data = error.response.data;
      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.details)) {
        message = data.details.map((d) => d.msg || JSON.stringify(d)).join(', ');
      } else if (data?.error) {
        message = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
      } else {
        message = `Server responded with HTTP ${error.response.status}`;
      }
    } else if (error.request) {
      message = 'Unable to reach backend server. Please verify backend is running on http://127.0.0.1:8000.';
    } else {
      message = error.message;
    }
    
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
