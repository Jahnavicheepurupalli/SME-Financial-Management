import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:5000') + '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Auto-attach JWT Token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Map HTTP errors to specific user-friendly messages
api.interceptors.response.use(
  (response) => response,
  (error) => {
    let customMessage = '';
    if (!error.response) {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        customMessage = "Unable to reach authentication service. Check your connection.";
      } else {
        customMessage = "Backend server is not running. Please start the Flask server.";
      }
    } else {
      // Prioritize explicit server error message
      const serverMsg = error.response.data?.message || error.response.data?.error;
      if (serverMsg) {
        customMessage = serverMsg;
      } else {
        const status = error.response.status;
        if (status === 400) {
          customMessage = "Validation failed. Please check your inputs.";
        } else if (status === 401) {
          customMessage = "Invalid email or password.";
        } else if (status === 404) {
          customMessage = "API endpoint not found.";
        } else if (status === 409) {
          customMessage = "Email already registered.";
        } else if (status === 500) {
          customMessage = "Internal server error. Please try again later.";
        } else {
          customMessage = error.message || "An unexpected error occurred.";
        }
      }
    }

    error.message = customMessage;
    if (error.response) {
      if (!error.response.data) {
        error.response.data = {};
      }
      error.response.data.message = customMessage;
    } else {
      error.response = {
        data: { message: customMessage }
      };
    }

    return Promise.reject(error);
  }
);

export default api;
