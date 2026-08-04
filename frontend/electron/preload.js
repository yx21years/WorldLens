// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  callApi: (endpoint, method = 'GET', body) => fetch(`http://localhost:8000${endpoint}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body : body ? JSON.stringify(body) : undefined,
  }).then(res => res.json()),
});
