#!/usr/bin/env python3
import socket
import pickle
import uvicorn
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Path to the config file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# Default RFCOMM port
RFCOMM_PORT = 4

app = FastAPI()

# Enable CORS for the Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Electron app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WiFiCredentials(BaseModel):
    ssid: str
    password: str

class fermiaConnect(BaseModel):
    ip: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

def load_config():
    """Load configuration from the config file."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    
    # Return empty config if file doesn't exist or there's an error
    return {}

@app.get("/")
async def root():
    """Root endpoint to check if server is running"""
    return {"status": "running"}

@app.post("/send-credentials")
async def send_credentials(credentials: WiFiCredentials):
    config = load_config()
    fermia_mac = config.get('fermiaMac')
    
    if not fermia_mac:
        raise HTTPException(
            status_code=400, 
            detail="Fermia MAC address not configured. Please set it in the Configuration tab."
        )
    
    try:
        # Create a Bluetooth socket
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((fermia_mac, RFCOMM_PORT))
        
        # Send WiFi credentials
        data = {"ssid": credentials.ssid, "password": credentials.password}
        sock.sendall(pickle.dumps(data))
        print(f"Credentials sent: SSID={credentials.ssid}")
        
        # Receive IP address
        print("Waiting for Fermia IP...")
        ip_data = sock.recv(4096)
        fermia_ip = pickle.loads(ip_data)
        sock.close()
        
        if fermia_ip:
            print(f"Received Fermia IP: {fermia_ip}")
            return {"success": True, "ip": fermia_ip}
        else:
            print("Did not receive a valid IP from Fermia.")
            return {"success": False, "message": "No valid IP received from Fermia."}
    except Exception as e:
        error_msg = f"Error communicating with Fermia: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/connect-fermia")
async def connect_fermia():
    try:
        # Load configuration
        config = load_config()
        
        # Check if we have all required configuration
        if not config.get('fermiaIp'):
            return {"success": False, "message": "Fermia IP not configured"}
        
        if not config.get('username'):
            return {"success": False, "message": "SSH username not configured"}
        
        if not config.get('password'):
            return {"success": False, "message": "SSH password not configured"}
        
        # Create the fermia_config.py file
        config_content = f'''# Auto-generated configuration file
FERMIA_IP = "{config.get('fermiaIp')}"
USERNAME = "{config.get('username')}"
PASSWORD = "{config.get('password')}"
'''
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fermia_config.py')
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Import the remote_ssh module and run the commands
        try:
            from remote_ssh import Program
            
            # Create a Program instance
            program = Program(config.get('username'), config.get('fermiaIp'), config.get('password'))
            
            # Connect to the Fermia
            program.connect()
            
            # Run the graph.py script
            program.spawn_command("python3 /home/arisenthil/fermia/graph.py")
            
            # Connect again (as in the original script)
            program.connect()
            
            # Run the streamlit app
            program.spawn_command("python3 -m streamlit run /home/arisenthil/fermia/app.py")
            
            # Return success
            return {
                "success": True, 
                "message": f"Streaming started. Visit http://{config.get('fermiaIp')}:8501"
            }
        
        except ImportError:
            return {
                "success": False, 
                "message": "Could not import remote_ssh module. Make sure it's installed."
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error executing remote commands: {str(e)}"}
        
    except Exception as e:
        error_msg = f"Error connecting to fermia: {str(e)}"
        print(error_msg)
        return {"success": False, "message": error_msg}

if __name__ == "__main__":
    print("Starting Bluetooth-FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)