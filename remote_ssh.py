import spur
import time
import os
import shlex

class Program:
    def __init__(self, username, hostname, password):
        self.hn = hostname
        self.user = username
        self.pas = password
        self.shell = None

    def connect(self):
        """ Establishes an SSH connection. """
        self.shell = spur.SshShell(
            hostname=self.hn,
            username=self.user,
            password=self.pas,
            missing_host_key=spur.ssh.MissingHostKey.accept
        )

    def retrieve(self, u_dir, remote_dir):
        """ Retrieves files from the remote system using SCP. """
        os.system(f'sshpass -p "{self.pas}" scp -r {self.user}@{self.hn}:{remote_dir} {u_dir}')

    def run_command(self, command):
        """ Runs a command on the remote machine and returns the output. """
        with self.shell:
            result = self.shell.run(command.split())
            return result.output.decode("utf-8")

    def run_program(self, command):
        """ Runs a command with an input variable on the remote machine and return the output."""
        with self.shell:
            result = self.shell.run(shlex.split(command))
            return result.output.decode("utf-8")

    def spawn_command(self, command):
        """ Spawns a long-running process on the remote machine. """
        with self.shell:
            process = self.shell.spawn(shlex.split(command))
            time.sleep(1)
            return process