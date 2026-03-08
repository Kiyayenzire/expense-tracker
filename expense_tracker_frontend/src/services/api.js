

// src/services/api.js

import axios from "axios";

// Use the configured API URL, or fall back to the default backend dev port.
// This avoids issues when the VITE_API_URL env var is not loaded.
const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

console.log("ENV VALUE:", apiUrl);

const api = axios.create({
  baseURL: apiUrl,
});

// Automatically attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;


