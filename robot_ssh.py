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


class SSHInteractive:
    """
    Fournit une session shell interactive via paramiko.
    - connect(): ouvre la connexion
    - start_shell(remote_cmd=None): ouvre un shell et exécute opcionallement remote_cmd
    - send(text): envoie du texte au shell (ajoute un \n si nécessaire)
    - set_output_callback(cb): callback appelée pour chaque bloc de sortie reçu (str)
    - close(): ferme la connexion
    """
    def __init__(self, hostname: str = "PEI.local", username: str = "admin",
                 password: str = "admin", port: int = 22, timeout: int = 10,
                 recv_buffer: int = 1024):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.recv_buffer = recv_buffer
        self._client: Optional[Any] = None
        self._chan = None
        self._out_cb = None
        self._reader_thread = None
        self._stop_reader = False

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

    def start_shell(self, remote_cmd: Optional[str] = None) -> None:
        if self._client is None:
            raise RuntimeError("Client SSH non connecté")
        # open a pty to have interactive behavior
        self._chan = self._client.invoke_shell()
        self._stop_reader = False
        # Optionally run a command after opening shell
        if remote_cmd:
            self.send(remote_cmd)

        # start reader thread
        def reader():
            try:
                while not self._stop_reader and self._chan and not self._chan.closed:
                    if self._chan.recv_ready():
                        data = self._chan.recv(self.recv_buffer)
                        if not data:
                            break
                        text = data.decode(errors='ignore')
                        if self._out_cb:
                            try:
                                self._out_cb(text)
                            except Exception:
                                pass
                    else:
                        time.sleep(0.05)
            except Exception:
                pass

        import threading
        self._reader_thread = threading.Thread(target=reader, daemon=True)
        self._reader_thread.start()

    def send(self, text: str) -> None:
        if self._chan is None:
            raise RuntimeError("Shell non démarrée")
        if not text.endswith('\n'):
            text = text + '\n'
        try:
            self._chan.send(text)
        except Exception as e:
            raise

    def set_output_callback(self, cb):
        self._out_cb = cb

    def close(self) -> None:
        try:
            self._stop_reader = True
            if self._reader_thread:
                self._reader_thread.join(timeout=0.5)
            if self._chan:
                try:
                    self._chan.close()
                except Exception:
                    pass
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    pass
        finally:
            self._chan = None
            self._client = None
            self._reader_thread = None
            self._out_cb = None

