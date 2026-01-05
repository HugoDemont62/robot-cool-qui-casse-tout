# Script de test mock pour SSHInteractive
# Injecte un faux module 'paramiko' dans sys.modules, recharge robot_ssh,
# et exécute une session interactive pour vérifier les callbacks.

import sys
import os
import types
import importlib
import time

# Ensure project root is on sys.path so imports like 'robot_ssh' work
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Crée un module paramiko factice
fake = types.ModuleType('paramiko')

class FakeChannel:
    def __init__(self):
        self._buf = [b'Mock: bienvenue sur le Raspberry\n', b'> ']  # quelques paquets
        self.closed = False
    def recv_ready(self):
        return bool(self._buf)
    def recv(self, n):
        if not self._buf:
            return b''
        data = self._buf.pop(0)
        return data
    def send(self, s):
        print(f"[FakeChannel] send: {s.strip()}")
    def close(self):
        self.closed = True

class FakeSSHClient:
    def __init__(self):
        self._chan = FakeChannel()
    def set_missing_host_key_policy(self, p):
        pass
    def connect(self, hostname, port, username, password, timeout):
        print(f"[FakeSSHClient] connect to {username}@{hostname}:{port} (timeout={timeout})")
    def invoke_shell(self):
        print("[FakeSSHClient] invoke_shell")
        return self._chan
    def exec_command(self, cmd):
        print(f"[FakeSSHClient] exec_command: {cmd}")
        # retourne des file-like objets (stdin, stdout, stderr); simulons
        return (None, types.SimpleNamespace(read=lambda : b"ok\n"), types.SimpleNamespace(read=lambda: b""))
    def close(self):
        print("[FakeSSHClient] close")

class FakeAutoAddPolicy:
    pass

fake.SSHClient = FakeSSHClient
fake.AutoAddPolicy = FakeAutoAddPolicy

# injecte dans sys.modules
sys.modules['paramiko'] = fake

# maintenant recharge robot_ssh
import robot_ssh
importlib.reload(robot_ssh)

print("=== Lancement du test mock SSHInteractive ===")

# crée la session
s = robot_ssh.SSHInteractive(hostname='PEI.local', username='admin', password='admin')
try:
    s.connect()
    # définir callback
    def cb(text):
        print(f"[callback] {text}")
    s.set_output_callback(cb)
    s.start_shell()
    time.sleep(0.2)
    s.send('echo hello from PC')
    time.sleep(0.2)
    s.send('MOVE forward 200')
    time.sleep(0.5)
finally:
    s.close()

print('=== Test mock terminé ===')
