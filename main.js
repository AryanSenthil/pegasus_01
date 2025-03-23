// main.js

const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const { loadConfig, saveConfig } = require('./config-manager');

// Path to the Python script
const pythonScriptPath = path.join(__dirname, 'bluetooth_server.py');
let mainWindow;
let pythonProcess = null;
let webviewWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 500,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  
  mainWindow.loadFile('index.html');

  // Start the Python backend 
  startPythonBackend();
}

function createWebViewWindow(url) {
  // Close existing webview window if it exists
  if (webviewWindow && !webviewWindow.isDestroyed()) {
    webviewWindow.close();
  }
  
  webviewWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webviewTag: true,
      webSecurity: false // Allows loading local content
    }
  });
  
  // Load HTML with embedded webview
  webviewWindow.loadFile('webview.html');
  
  // Wait for the window to finish loading
  webviewWindow.webContents.on('did-finish-load', () => {
    // Send the URL to navigate to
    webviewWindow.webContents.send('load-url', url);
  });
  
  // Enable debugging in the webview if needed
  // webviewWindow.webContents.openDevTools();
  
  webviewWindow.on('closed', () => {
    webviewWindow = null;
  });
}

function startPythonBackend() {
  // Check if the Python process is already running 
  if (pythonProcess) {
    console.log('Python backend is already running');
    return;
  }

  console.log('Starting Python backend...');

  // First, try with python3
  try {
    pythonProcess = spawn('python3', [pythonScriptPath]);
  } catch (error) {
    console.log('Failed to start with python3, trying python...');
    try {
      pythonProcess = spawn('python', [pythonScriptPath]);
    } catch (innerError) {
      console.log('Failed to start Python backend:', innerError);
      if (mainWindow) {
        mainWindow.webContents.send('backend-status', { 
          status: 'error',
          error: 'Failed to start Python backend. Make sure Python is installed.'
        });
      }
      return;
    }
  }

  // Flag to check if server is ready
  let serverReady = false;

  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    console.log(`Python backend output: ${output}`);

    // Check if the server is up and running
    if (output.includes('Uvicorn running on http://127.0.0.1:8000')) {
      serverReady = true;
      if (mainWindow) {
        mainWindow.webContents.send('backend-status', { status: 'ready' });
      }
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python backend error: ${data.toString()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python backend process exited with code ${code}`);
    pythonProcess = null;
    if (mainWindow) {
      mainWindow.webContents.send('backend-status', { 
        status: 'stopped',
        error: code !== 0 ? `Process exited with code ${code}` : null
      });
    }
  });

  // Check if server is running after a delay 
  setTimeout(async () => {
    if (!serverReady) {
      try {
        await axios.get('http://localhost:8000/');
        serverReady = true;
        if (mainWindow) {
          mainWindow.webContents.send('backend-status', { status: 'ready' });
        }
      } catch (err) {
        console.error('Python backend not responding:', err.message);
        if (mainWindow) {
          mainWindow.webContents.send('backend-status', {
            status: 'error',
            error: 'Failed to connect to Python backend. Make sure Python and required packages are installed.'
          });
        }
      }
    }
  }, 5000); // Increased timeout to 5 seconds
}

// Handle config loading request from renderer
ipcMain.handle('load-config', async () => {
  return loadConfig();
});

// Handle config saving request from renderer
ipcMain.handle('save-config', async (event, config) => {
  return saveConfig(config);
});

// Handle API requests from the renderer for WiFi credentials
ipcMain.handle('send-credentials', async (event, credentials) => {
  try {
    // Make sure fermiaMac is saved first
    const config = loadConfig();
    config.fermiaMac = credentials.fermiaMac;
    saveConfig(config);
    
    // Then send to Python backend
    const response = await axios.post('http://localhost:8000/send-credentials', {
      ssid: credentials.ssid,
      password: credentials.password
    });
    
    // If successful, update the config with the new values
    if (response.data.success) {
      const config = loadConfig();
      config.wifiSsid = credentials.ssid;
      config.wifiPassword = credentials.password;
      
      // If we received a new IP, update that too
      if (response.data.ip) {
        config.fermiaIp = response.data.ip;
      }
      
      saveConfig(config);
    }
    
    return response.data;
  } catch (error) {
    console.error('Error sending credentials:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || 'Failed to communicate with Python backend'
    };
  }
});

// Handle connect to Fermia SSH request
ipcMain.handle('connect-fermia', async () => {
  try {
    const response = await axios.post('http://localhost:8000/connect-fermia');
    
    if (response.data.success) {
      // Get the URL from the response
      const config = loadConfig();
      const streamlitUrl = `http://${config.fermiaIp}:8501`;
      
      // Create a new window with embedded webview
      createWebViewWindow(streamlitUrl);
    }
    
    return response.data;
  } catch (error) {
    console.error('Error connecting to Fermia:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || 'Failed to communicate with Python backend'
    };
  }
});

// Handle opening URL in webview
ipcMain.handle('open-webview', async (event, url) => {
  createWebViewWindow(url);
  return { success: true };
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  // Kill the Python process when the app is closed
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  // Make sure to kill the Python process when the app is about to quit
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
});