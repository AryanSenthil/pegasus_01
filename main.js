const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

// Path to the Python script
const pythonScriptPath = path.join(__dirname, 'bluetooth_server.py');

let mainWindow;
let pythonProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 400,
    height: 350,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');
  
  // Start the Python backend
  startPythonBackend();
}

function startPythonBackend() {
  // Check if the Python process is already running
  if (pythonProcess) {
    console.log('Python backend is already running');
    return;
  }

  // Start the Python FastAPI server
  console.log('Starting Python backend...');
  
  // Use 'python' or 'python3' depending on your system
  pythonProcess = spawn('python3', [pythonScriptPath]);

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
  }, 3000);
}

// Handle API requests from the renderer
ipcMain.handle('send-credentials', async (event, credentials) => {
  try {
    const response = await axios.post('http://localhost:8000/send-credentials', credentials);
    return response.data;
  } catch (error) {
    console.error('Error sending credentials:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || 'Failed to communicate with Python backend'
    };
  }
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