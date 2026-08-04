const { app, BrowserWindow, protocol } = require('electron');
const path = require('path');
const http = require('http');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = process.env.NODE_ENV === 'dev' ? 'http://localhost:3000' : `file://${path.join(__dirname, '../backend/static/index.html')}`;
  mainWindow.loadURL(devUrl);

  if (process.env.NODE_ENV === 'dev') {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);
