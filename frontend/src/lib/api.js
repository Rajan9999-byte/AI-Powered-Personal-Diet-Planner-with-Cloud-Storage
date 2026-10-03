export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function request(path, options = {}) {
  const headers = { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...(options.headers || {}) };
  const response = await fetch(path, { credentials: 'same-origin', ...options, headers });
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { error: text || 'The server returned an unreadable response.' };
  }
  if (!response.ok) {
    throw new ApiError(payload.error || `Request failed (${response.status}).`, response.status);
  }
  return payload;
}

const json = (method, body) => ({ method, body: JSON.stringify(body) });

export const api = {
  me: () => request('/api/auth/me'),
  register: (body) => request('/api/auth/register', json('POST', body)),
  login: (body) => request('/api/auth/login', json('POST', body)),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  getProfile: () => request('/api/profile'),
  saveProfile: (body) => request('/api/profile', json('PUT', body)),
  getTargets: (profile) => request('/api/targets', json('POST', { profile })),
  getDashboard: () => request('/api/dashboard'),
  getPlans: () => request('/api/plans'),
  createPlan: (targets) => request('/api/plans', json('POST', { targets })),
  getFoods: () => request('/api/foods'),
  getIntake: (date) => request(`/api/intake?date=${encodeURIComponent(date)}`),
  addIntake: (body) => request('/api/intake', json('POST', body)),
  deleteIntake: (id) => request(`/api/intake/${id}`, { method: 'DELETE' }),
  uploadProfilePhoto: (file) => {
    const data = new FormData();
    data.append('file', file);
    return request('/api/storage/profile-photo', { method: 'POST', body: data });
  }
};
