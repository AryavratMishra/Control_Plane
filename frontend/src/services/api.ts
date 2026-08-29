export const API_BASE = import.meta.env.VITE_API_URL || '';
export const WS_BASE = import.meta.env.VITE_WS_URL || '';

const api = {
  async get(path: string) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
  },
  async post(path: string, body: unknown) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
  },
};

export default api;

// Dashboard
export const getDashboard = () => api.get('/api/v1/dashboard/summary');

// Incidents
export const getIncidents = (params?: Record<string, string>) => {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return api.get(`/api/v1/incidents${qs}`);
};
export const getIncident = (id: string) => api.get(`/api/v1/incidents/${id}`);
export const reviewIncident = (id: string, body: { action: string; comment: string; reviewer_name: string; was_correct: string }) =>
  api.post(`/api/v1/incidents/${id}/review`, body);

// Policies
export const getPolicies = () => api.get('/api/v1/policies');

// Demo
export const runDemo = (scenario: string) => api.post(`/api/v1/demo/run/${scenario}`, {});
export const getScenarios = () => api.get('/api/v1/demo/scenarios');

// Evaluate
export const evaluate = (body: unknown) => api.post('/api/v1/gateway/evaluate', body);
