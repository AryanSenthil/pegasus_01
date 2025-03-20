// Run this script with Node.js to check if Python and required packages are installed
// Usage: node check_python.js

const { spawn } = require('child_process');

console.log('Checking Python installation...');

// Check Python version
const checkPython = spawn('python3', ['--version']);
checkPython.stdout.on('data', (data) => {
  console.log(`Python version: ${data}`);
});
checkPython.stderr.on('data', (data) => {
  console.error(`Error checking Python version: ${data}`);
});
checkPython.on('close', (code) => {
  if (code !== 0) {
    console.log('Python3 not found, trying python...');
    
    const checkPythonAlt = spawn('python', ['--version']);
    
    checkPythonAlt.stdout.on('data', (data) => {
      console.log(`Python version: ${data}`);
    });
    
    checkPythonAlt.stderr.on('data', (data) => {
      console.error(`Error checking Python version: ${data}`);
    });
    
    checkPythonAlt.on('close', (code) => {
      if (code !== 0) {
        console.error('Python is not installed or not in the PATH. Please install Python 3.');
        process.exit(1);
      } else {
        checkPackages('python');
      }
    });
  } else {
    checkPackages('python3');
  }
});

function checkPackages(pythonCmd) {
  console.log('\nChecking required packages...');
  
  // Check FastAPI
  const checkFastAPI = spawn(pythonCmd, ['-c', 'import fastapi; print(f"FastAPI version: {fastapi.__version__}")']);
  
  checkFastAPI.stdout.on('data', (data) => {
    console.log(`${data}`);
  });
  
  checkFastAPI.stderr.on('data', (data) => {
    console.error('FastAPI is not installed. Please install it with:');
    console.error('pip install fastapi uvicorn pydantic');
  });
  
  // Check if Bluetooth libraries are available
  console.log('\nChecking Bluetooth support...');
  const checkBluetooth = spawn(pythonCmd, ['-c', `
import socket
try:
    socket.AF_BLUETOOTH
    print("Python Bluetooth support: Available")
except AttributeError:
    print("Python Bluetooth support: Not available - Socket module does not support Bluetooth")
  `]);
  
  checkBluetooth.stdout.on('data', (data) => {
    console.log(`${data}`);
  });
  
  checkBluetooth.stderr.on('data', (data) => {
    console.error(`Error checking Bluetooth support: ${data}`);
  });
}