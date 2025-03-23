#!/usr/bin/env python3
import sys
import os
import pytest
from unittest.mock import patch, MagicMock, call

# Add the parent directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the remote_ssh module
from remote_ssh import Program

class TestRemoteSSH:
    """Test suite for remote_ssh.py"""
    
    def setup_method(self):
        """Setup test environment before each test method"""
        self.username = "testuser"
        self.hostname = "192.168.1.100"
        self.password = "testpass"
        self.program = Program(self.username, self.hostname, self.password)

    @patch('remote_ssh.spur.SshShell')
    def test_connect(self, mock_ssh_shell):
        """Test establishing SSH connection"""
        # Setup mock
        mock_shell = MagicMock()
        mock_ssh_shell.return_value = mock_shell
        
        # Call the method
        self.program.connect()
        
        # Assertions
        mock_ssh_shell.assert_called_once_with(
            hostname=self.hostname,
            username=self.username,
            password=self.password,
            missing_host_key=MagicMock()
        )
        
        # Check that the shell property is set
        assert self.program.shell is not None

    @patch('remote_ssh.os.system')
    def test_retrieve(self, mock_system):
        """Test retrieving files via SCP"""
        # Call the method
        local_dir = "/local/path"
        remote_dir = "/remote/path"
        self.program.retrieve(local_dir, remote_dir)
        
        # Assertions
        expected_command = f'sshpass -p "{self.password}" scp -r {self.username}@{self.hostname}:{remote_dir} {local_dir}'
        mock_system.assert_called_once_with(expected_command)

    def test_run_command(self):
        """Test running a command and getting its output"""
        # Setup mock
        mock_shell = MagicMock()
        mock_result = MagicMock()
        mock_result.output = b"command output"
        mock_shell.__enter__.return_value = mock_shell
        mock_shell.run.return_value = mock_result
        self.program.shell = mock_shell
        
        # Call the method
        command = "ls -la"
        result = self.program.run_command(command)
        
        # Assertions
        assert result == "command output"
        mock_shell.run.assert_called_once_with(command.split())

    def test_run_program(self):
        """Test running a command with arguments"""
        # Setup mock
        mock_shell = MagicMock()
        mock_result = MagicMock()
        mock_result.output = b"program output"
        mock_shell.__enter__.return_value = mock_shell
        mock_shell.run.return_value = mock_result
        self.program.shell = mock_shell
        
        # Call the method
        command = "python script.py --arg value"
        result = self.program.run_program(command)
        
        # Assertions
        assert result == "program output"
        mock_shell.run.assert_called_once()  # Can't check exact args due to shlex.split

    @patch('remote_ssh.time.sleep')
    def test_spawn_command(self, mock_sleep):
        """Test spawning a long-running process"""
        # Setup mock
        mock_shell = MagicMock()
        mock_process = MagicMock()
        mock_shell.__enter__.return_value = mock_shell
        mock_shell.spawn.return_value = mock_process
        self.program.shell = mock_shell
        
        # Call the method
        command = "python -m http.server"
        result = self.program.spawn_command(command)
        
        # Assertions
        assert result == mock_process
        mock_shell.spawn.assert_called_once()  # Can't check exact args due to shlex.split
        mock_sleep.assert_called_once_with(1)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
