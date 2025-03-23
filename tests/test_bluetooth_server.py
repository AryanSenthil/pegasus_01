#!/usr/bin/env python3
import sys
import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the FastAPI app
from bluetooth_server import app, WiFiCredentials, load_config, save_config

# Create a test client
client = TestClient(app)

# Test data
mock_config = {
    "fermiaIp": "192.168.1.100",
    "fermiaMac": "00:11:22:33:44:55",
    "username": "testuser",
    "password": "testpass"
}

def test_root_endpoint():
    """Test the root endpoint returns correct status"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}

@patch('bluetooth_server.load_config')
def test_send_credentials_missing_mac(mock_load_config):
    """Test sending credentials without MAC address configured"""
    # Return config without MAC address
    mock_load_config.return_value = {"fermiaIp": "192.168.1.100"}
    
    response = client.post(
        "/send-credentials",
        json={"ssid": "TestWiFi", "password": "testpassword"}
    )
    
    assert response.status_code == 400
    assert "MAC address not configured" in response.json()["detail"]

@patch('bluetooth_server.socket.socket')
@patch('bluetooth_server.load_config')
@patch('bluetooth_server.save_config')
def test_send_credentials_success(mock_save_config, mock_load_config, mock_socket):
    """Test sending credentials with successful Bluetooth connection"""
    # Mock the socket instance
    mock_sock_instance = MagicMock()
    mock_socket.return_value = mock_sock_instance
    
    # Mock pickle.loads to return an IP
    with patch('bluetooth_server.pickle.loads', return_value="192.168.1.200"):
        # Configure mocks
        mock_load_config.return_value = mock_config
        mock_save_config.return_value = True
        
        # Test the endpoint
        response = client.post(
            "/send-credentials",
            json={"ssid": "TestWiFi", "password": "testpassword"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": True, "ip": "192.168.1.200"}
        mock_sock_instance.connect.assert_called_once()
        mock_sock_instance.sendall.assert_called_once()
        mock_save_config.assert_called_once()

@patch('bluetooth_server.socket.socket')
@patch('bluetooth_server.load_config')
def test_send_credentials_timeout(mock_load_config, mock_socket):
    """Test sending credentials with Bluetooth timeout"""
    # Mock the socket instance
    mock_sock_instance = MagicMock()
    mock_socket.return_value = mock_sock_instance
    
    # Configure socket to raise timeout
    mock_sock_instance.recv.side_effect = TimeoutError("Timeout")
    
    # Configure mocks
    mock_load_config.return_value = mock_config
    
    # Test the endpoint
    response = client.post(
        "/send-credentials",
        json={"ssid": "TestWiFi", "password": "testpassword"}
    )
    
    # Assertions
    assert response.status_code in [408, 500]  # Either timeout or internal error
    mock_sock_instance.connect.assert_called_once()
    mock_sock_instance.sendall.assert_called_once()

@patch('bluetooth_server.load_config')
def test_connect_fermia_missing_config(mock_load_config):
    """Test connecting to Fermia with missing configuration"""
    # Cases to test: missing IP, username, password
    
    # Test missing IP
    mock_load_config.return_value = {"username": "user", "password": "pass"}
    response = client.post("/connect-fermia")
    assert response.status_code == 200
    assert response.json() == {"success": False, "message": "Fermia IP not configured"}
    
    # Test missing username
    mock_load_config.return_value = {"fermiaIp": "192.168.1.100", "password": "pass"}
    response = client.post("/connect-fermia")
    assert response.status_code == 200
    assert response.json() == {"success": False, "message": "SSH username not configured"}
    
    # Test missing password
    mock_load_config.return_value = {"fermiaIp": "192.168.1.100", "username": "user"}
    response = client.post("/connect-fermia")
    assert response.status_code == 200
    assert response.json() == {"success": False, "message": "SSH password not configured"}

@patch('bluetooth_server.load_config')
@patch('builtins.open', new_callable=mock_open)
@patch('bluetooth_server.Program')
def test_connect_fermia_success(mock_program_class, mock_file_open, mock_load_config):
    """Test connecting to Fermia with successful SSH connection"""
    # Configure mocks
    mock_load_config.return_value = mock_config
    mock_program = MagicMock()
    mock_program_class.return_value = mock_program
    mock_program.run_command.return_value = "SSH connection test"
    
    # Test the endpoint
    with patch('bluetooth_server.time.sleep'):  # Mock sleep to speed up test
        response = client.post("/connect-fermia")
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "Streaming started" in response.json()["message"]
    mock_program.connect.assert_called()
    mock_program.spawn_command.assert_called()

@patch('bluetooth_server.os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data=json.dumps(mock_config))
def test_load_config_success(mock_file, mock_exists):
    """Test loading configuration successfully"""
    mock_exists.return_value = True
    config = load_config()
    assert config == mock_config
    mock_file.assert_called_once()

@patch('bluetooth_server.os.path.exists')
def test_load_config_no_file(mock_exists):
    """Test loading configuration when file doesn't exist"""
    mock_exists.return_value = False
    config = load_config()
    assert config == {}

@patch('builtins.open', new_callable=mock_open)
def test_save_config_success(mock_file):
    """Test saving configuration successfully"""
    result = save_config(mock_config)
    assert result is True
    mock_file.assert_called_once()
    mock_file().write.assert_called_once()

@patch('builtins.open')
def test_save_config_failure(mock_open):
    """Test saving configuration with failure"""
    mock_open.side_effect = Exception("Write error")
    result = save_config(mock_config)
    assert result is False

if __name__ == "__main__":
    pytest.main(["-v", __file__])
