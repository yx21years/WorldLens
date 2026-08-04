import { ipcRenderer } from 'electron';

// Expose a safe IPC method for the React app to call backend API directly
async function callApi(endpoint: string, method: string = 'GET', body?: any) {
  const response = await fetch(`http://localhost:8000${endpoint}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return response.json();
}

export const api = {
  health: () => callApi('/health'),
  articles: (params?: any) => callApi('/api/v1/articles', 'GET', params),
};
export default api;