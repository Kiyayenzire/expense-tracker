import axios from 'axios';

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export function createClient(token) {
  return axios.create({
    baseURL: apiBase,
    headers: {
      Authorization: token ? `Token ${token}` : undefined,
      'Content-Type': 'application/json',
    },
  });
}

export function formatDateEU(value) {
  if (!value) return '';
  const date = new Date(value);
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}
