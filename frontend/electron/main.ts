import path from 'path';
import { app, BrowserWindow, protocol } from 'electron';
import * as fs from 'fs';

let mainWindow: BrowserWindow;

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Load React dev server or production build
  const devUrl = 'http://localhost:3000';
  const productionPath = path.join(__dirname, '../backend/static/index.html');

  if (process.env.NODE_ENV === 'dev') {
    mainWindow.loadURL(devUrl);
  } else {
    mainWindow.loadFile(productionPath);
  };

  // Enable DevTools in development
  if (process.env.NODE_ENV === 'dev') {
    mainWindow.webContents.openDevTools();
  }
};

app.whenReady().then(createWindow);
