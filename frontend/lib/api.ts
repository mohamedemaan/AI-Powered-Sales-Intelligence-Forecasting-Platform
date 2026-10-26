import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically attach JWT token and active organization context to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    const activeOrgId = localStorage.getItem("active_organization_id");
    if (activeOrgId) {
      config.headers["X-Organization-ID"] = activeOrgId;
    }
  }
  return config;
});

export default api;
