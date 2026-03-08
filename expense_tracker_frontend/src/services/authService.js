

// src/services/authService.js

import api from "./api";

/*
Centralized authentication API service.

Important:
The system requires real email addresses because the backend
sends activation links via email. Fake emails would prevent
users from activating their accounts.
*/

// STEP 1 — EMAIL VALIDATION
export const checkEmail = async (email) => {
  const response = await api.post("/api/users/check-email/", { email });
  return response.data;
};

// STEP 2 — REGISTER USER
export const register = async (data) => {
  const response = await api.post("/api/users/register/", data);
  return response.data;
};

// LOGIN USER
export const login = async (email, password) => {
  const response = await api.post("/api/users/login/", {
    email,
    password,
  });

  const { access, refresh } = response.data;

  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);

  return response.data;
};

// GET CURRENT USER
export const getCurrentUser = async () => {
  const response = await api.get("/api/users/me/");
  return response.data;
};

// LOGOUT
export const logout = () => {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
};

