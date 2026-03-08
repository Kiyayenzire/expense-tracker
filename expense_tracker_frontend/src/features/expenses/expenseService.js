

// src/features/expenses/expenseService.js

import api from "../../services/api";

// Fetch expenses for a given date
export const getExpensesByDate = async (date) => {
  const response = await api.get(`/api/expenses/expenses/?date=${date}`);
  const data = response.data;
  return data.results || data; // handle paginated and non-paginated responses
};

// Create a new expense
export const createExpense = async (expenseData) => {
  const response = await api.post(`/api/expenses/expenses/`, expenseData);
  return response.data;
};

// Fetch categories (sections)
export const getSections = async () => {
  const response = await api.get("/api/sections/");
  return response.data;
};

// Fetch subcategories
export const getSubsections = async (sectionId) => {
  const response = await api.get(`/api/sections/${sectionId}/subsections/`);
  return response.data;
};

// Fetch items
export const getItems = async () => {
  const response = await api.get("/api/items/");
  return response.data;
};


