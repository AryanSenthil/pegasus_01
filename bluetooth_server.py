#!/usr/bin/env python3
import socket
import pickle
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Replace with your Jetson's Bluetooth MAC address
JETSON_MAC = "28:D0:43:1D:09:34"
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

@app.get("/")
async def root():
    """Root endpoint to check if server is running"""
    return {"status": "running"}

@app.post("/send-credentials")
async def send_credentials(credentials: WiFiCredentials):
    try:
        # Create a Bluetooth socket
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((JETSON_MAC, RFCOMM_PORT))

        # Send WiFi credentials
        data = {"ssid": credentials.ssid, "password": credentials.password}
        sock.sendall(pickle.dumps(data))
        print(f"Credentials sent: SSID={credentials.ssid}")
        
        # Receive IP address
        print("Waiting for Jetson IP...")
        ip_data = sock.recv(4096)
        jetson_ip = pickle.loads(ip_data)
        sock.close()
        print(jetson_ip)
        
        if jetson_ip:
            print(f"Received Jetson IP: {jetson_ip}")
            return {"success": True, "ip": jetson_ip}
        else:
            print("Did not receive a valid IP from Jetson.")
            return {"success": False, "message": "No valid IP received from Jetson."}
            
    except Exception as e:
        error_msg = f"Error communicating with Jetson: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    print("Starting Bluetooth-FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)