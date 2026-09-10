import axios from 'axios';

const rawApiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').trim();
const apiBase = rawApiBase
  .replace(/\/api\/expenses\/?$/i, '/api')
  .replace(/\/expenses\/?$/i, '')
  .replace(/\/+$/, '');

export function getApiBase() {
  return apiBase;
}

export function buildApiUrl(path = '') {
  const cleanedPath = String(path).replace(/^\/+/, '');
  return cleanedPath ? `${apiBase}/${cleanedPath}` : apiBase;
}

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
  if (!value || typeof value !== 'string') {
    return '-';
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return '-';
  }

  try {
    let date;

    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      const [year, month, day] = trimmed.split('-').map(Number);
      date = new Date(year, month - 1, day);
    } else if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(trimmed)) {
      const [day, month, year] = trimmed.split('/').map(Number);
      date = new Date(year, month - 1, day);
    } else {
      date = new Date(trimmed);
    }

    if (!date || Number.isNaN(date.getTime())) {
      console.warn('Invalid date - NaN timestamp:', value);
      return '-';
    }

    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(date);
  } catch (error) {
    console.warn('Error formatting date:', value, error.message);
    return '-';
  }
}
