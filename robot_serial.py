"""
robot_serial.py

Module pour la communication série directe avec l'Arduino.
Permet d'envoyer des commandes au robot sans passer par SSH.

Auteur: Hugo Demont
Version: 1.0.0
"""

import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Callable, List
from dataclasses import dataclass


@dataclass
class SerialCommand:
    """Représente une commande série à envoyer à l'Arduino."""
    command: str
    expected_response: str = "OK"
    timeout: float = 1.0


class RobotSerial:
    """
    Gère la communication série avec l'Arduino du robot.
    
    Exemples d'utilisation:
        robot = RobotSerial()
        robot.connect("/dev/ttyACM0")  # ou "COM3" sur Windows
        robot.send_command("MOVE forward 200")
        robot.send_command("ClampGrab 5")
        robot.disconnect()
    """
    
    def __init__(self, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialise le gestionnaire de communication série.
        
        Args:
            baudrate: Vitesse de communication (doit correspondre à l'Arduino)
            timeout: Timeout pour les opérations de lecture
        """
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._connected = False
        self._response_callback: Optional[Callable[[str], None]] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_reader = False
        
    @staticmethod
    def list_available_ports() -> List[str]:
        """
        Liste tous les ports série disponibles sur le système.
        
        Returns:
            Liste des noms de ports disponibles
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def connect(self, port: str) -> bool:
        """
        Connecte au port série spécifié.
        
        Args:
            port: Nom du port série (ex: "/dev/ttyACM0" ou "COM3")
            
        Returns:
            True si la connexion a réussi, False sinon
        """
        try:
            if self._connected:
                self.disconnect()
            
            self._serial = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Attendre que l'Arduino soit prêt
            time.sleep(2)
            
            # Vider le buffer
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            
            self._connected = True
            self._start_reader()
            
            print(f"✅ Connecté au port {port}")
            return True
            
        except serial.SerialException as e:
            print(f"❌ Erreur de connexion au port {port}: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Déconnecte du port série."""
        self._stop_reader = True
        
        if self._reader_thread:
            self._reader_thread.join(timeout=1.0)
            self._reader_thread = None
        
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                print("🔌 Déconnecté du port série")
            except Exception as e:
                print(f"⚠️ Erreur lors de la déconnexion: {e}")
        
        self._serial = None
        self._connected = False
    
    def is_connected(self) -> bool:
        """Vérifie si le port série est connecté."""
        return self._connected and self._serial is not None and self._serial.is_open
    
    def send_command(self, command: str, wait_response: bool = True) -> Optional[str]:
        """
        Envoie une commande à l'Arduino.
        
        Args:
            command: La commande à envoyer (ex: "MOVE forward 200")
            wait_response: Si True, attend la réponse de l'Arduino
            
        Returns:
            La réponse de l'Arduino si wait_response=True, None sinon
        """
        if not self.is_connected():
            print("❌ Non connecté au robot")
            return None
        
        try:
            # Ajouter un retour à la ligne si nécessaire
            if not command.endswith('\n'):
                command += '\n'
            
            # Envoyer la commande
            self._serial.write(command.encode())
            
            if wait_response:
                # Attendre la réponse
                response = self._serial.readline().decode().strip()
                
                if self._response_callback:
                    self._response_callback(f"> {command.strip()} → {response}")
                
                return response
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de la commande: {e}")
            return None
    
    def set_response_callback(self, callback: Callable[[str], None]):
        """
        Définit une fonction de callback pour les réponses reçues.
        
        Args:
            callback: Fonction appelée avec la réponse en paramètre
        """
        self._response_callback = callback
    
    def _start_reader(self):
        """Démarre le thread de lecture des réponses."""
        def reader():
            while not self._stop_reader and self.is_connected():
                try:
                    if self._serial.in_waiting > 0:
                        line = self._serial.readline().decode().strip()
                        if line and self._response_callback:
                            self._response_callback(line)
                except Exception as e:
                    if not self._stop_reader:
                        print(f"⚠️ Erreur de lecture: {e}")
                time.sleep(0.01)
        
        self._stop_reader = False
        self._reader_thread = threading.Thread(target=reader, daemon=True)
        self._reader_thread.start()
    
    # ===== COMMANDES PRÉDÉFINIES =====
    
    def move_forward(self, speed: int = 200):
        """Avancer."""
        return self.send_command(f"MOVE forward {speed}")
    
    def move_backward(self, speed: int = 200):
        """Reculer."""
        return self.send_command(f"MOVE backward {speed}")
    
    def move_left(self, speed: int = 200):
        """Translation vers la gauche."""
        return self.send_command(f"MOVE left {speed}")
    
    def move_right(self, speed: int = 200):
        """Translation vers la droite."""
        return self.send_command(f"MOVE right {speed}")
    
    def rotate_cw(self, speed: int = 200):
        """Rotation horaire."""
        return self.send_command(f"MOVE rotateCW {speed}")
    
    def rotate_ccw(self, speed: int = 200):
        """Rotation anti-horaire."""
        return self.send_command(f"MOVE rotateCCW {speed}")
    
    def stop_all(self):
        """Arrêter tous les moteurs."""
        return self.send_command("MOVE stop 0")
    
    def clamp_rotate(self):
        """Rotation de la pince."""
        return self.send_command("ClampRotate")
    
    def clamp_origin(self):
        """Réinitialiser la position de la pince."""
        return self.send_command("ClampOrigin")
    
    def clamp_find_origin(self):
        """Trouver l'origine de la pince avec le capteur."""
        return self.send_command("ClampFindOrigin")
    
    def clamp_up(self, mm: Optional[int] = None):
        """Lever la pince."""
        cmd = "ClampUp" if mm is None else f"ClampUp {mm}"
        return self.send_command(cmd)
    
    def clamp_down(self, mm: Optional[int] = None):
        """Abaisser la pince."""
        cmd = "ClampDown" if mm is None else f"ClampDown {mm}"
        return self.send_command(cmd)
    
    def clamp_grab(self, mm: Optional[int] = None):
        """Fermer la pince."""
        cmd = "ClampGrab" if mm is None else f"ClampGrab {mm}"
        return self.send_command(cmd)
    
    def clamp_release(self, mm: Optional[int] = None):
        """Ouvrir la pince."""
        cmd = "ClampRelease" if mm is None else f"ClampRelease {mm}"
        return self.send_command(cmd)
    
    def clamp_move_to(self, mm: int):
        """Déplacer la pince à une position spécifique."""
        return self.send_command(f"ClampMoveTo {mm}")
    
    def set_pin(self, pin: int, state: int):
        """Contrôler une pin numérique."""
        return self.send_command(f"SET_PIN {pin} {state}")
    
    def set_pwm(self, pin: int, value: int):
        """Contrôler une pin PWM."""
        return self.send_command(f"SET_PWM {pin} {value}")


# ===== EXEMPLE D'UTILISATION =====

if __name__ == "__main__":
    print("🤖 Test de communication série avec l'Arduino")
    print("=" * 50)
    
    # Lister les ports disponibles
    ports = RobotSerial.list_available_ports()
    print(f"\nPorts série disponibles: {ports}")
    
    if not ports:
        print("❌ Aucun port série trouvé!")
        exit(1)
    
    # Créer l'instance
    robot = RobotSerial()
    
    # Callback pour afficher les réponses
    robot.set_response_callback(lambda msg: print(f"📨 {msg}"))
    
    # Utiliser le premier port disponible (ou spécifier manuellement)
    port = ports[0]  # Modifier si nécessaire (ex: "/dev/ttyACM0" ou "COM3")
    
    if robot.connect(port):
        try:
            print("\n🧪 Test des commandes...")
            
            # Test mouvement
            print("\n1️⃣ Avancer 2 secondes...")
            robot.move_forward(150)
            time.sleep(2)
            robot.stop_all()
            
            time.sleep(1)
            
            # Test rotation
            print("\n2️⃣ Rotation 2 secondes...")
            robot.rotate_cw(150)
            time.sleep(2)
            robot.stop_all()
            
            time.sleep(1)
            
            # Test pince
            print("\n3️⃣ Test pince...")
            robot.clamp_grab(5)
            time.sleep(1)
            robot.clamp_release(5)
            
            print("\n✅ Tests terminés!")
            
        except KeyboardInterrupt:
            print("\n⚠️ Interruption par l'utilisateur")
        
        finally:
            robot.stop_all()
            robot.disconnect()
    else:
        print(f"❌ Impossible de se connecter au port {port}")
