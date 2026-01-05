"""
robot_ssh.py

Wrapper minimal pour lancer un script distant sur le Raspberry Pi (PEI)
via SSH en utilisant paramiko. Fournit une fonction `start_test_on_pi`
utilisée par `main.py`.

Remarques:
- Par défaut: hostname=PEI.local, username=admin, password=admin
- Lance `python3 <remote_path>` en arrière-plan via nohup et enregistre
  la sortie dans ~/test_remote_<timestamp>.log
- Lève des exceptions si la connexion ou l'exécution échoue.
"""

import time
import os
from typing import Optional, Any

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except Exception:
    paramiko = None
    PARAMIKO_AVAILABLE = False


class SSHRunner:
    def __init__(self, hostname: str = "PEI.local", username: str = "admin",
                 password: str = "admin", port: int = 22, timeout: int = 10):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        # Use Any for the client type to avoid static-type warnings when
        # paramiko isn't installed in the development environment.
        self._client: Optional[Any] = None

    def connect(self) -> None:
        if not PARAMIKO_AVAILABLE:
            raise RuntimeError("paramiko n'est pas installé; ajoutez-le à requirements.txt")
        if self._client is not None:
            return
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.hostname, port=self.port,
                       username=self.username, password=self.password,
                       timeout=self.timeout)
        self._client = client

    def run_remote_script(self, remote_path: str = "test.py", logfile_prefix: str = "test_remote") -> str:
        if self._client is None:
            raise RuntimeError("Client SSH non connecté")
        timestamp = int(time.time())
        logfile = f"~/{logfile_prefix}_{timestamp}.log"
        # Si remote_path est absolu, n'effectue pas cd ~
        if os.path.isabs(remote_path):
            cmd = f"nohup python3 {remote_path} > {logfile} 2>&1 &"
        else:
            cmd = f"cd ~ && nohup python3 {remote_path} > {logfile} 2>&1 &"
        stdin, stdout, stderr = self._client.exec_command(cmd)
        # On retourne le chemin du logfile pour information.
        return logfile

    def close(self) -> None:
        try:
            if self._client:
                self._client.close()
        finally:
            self._client = None


def start_test_on_pi(hostname: str = "PEI.local", username: str = "admin",
                     password: str = "admin", remote_path: str = "test.py") -> str:
    """
    Connexion au Raspberry et lancement de `test.py` en arrière-plan.
    Retourne le chemin du logfile distant où stdout/stderr sont redirigés.
    Lève une exception si la connexion/exécution échoue.
    """
    runner = SSHRunner(hostname=hostname, username=username, password=password)
    try:
        runner.connect()
        logfile = runner.run_remote_script(remote_path)
        return logfile
    finally:
        runner.close()
