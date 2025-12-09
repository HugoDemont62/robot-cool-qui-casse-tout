"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ROBOT STATE - EUROBOT 2026                           ║
║                      Équipe: Pas encore ingénieur                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Fichier: robot_state.py
Auteur: Hugo Demont
Version: 1.0.0

DESCRIPTION:
    Ce module gère l'état complet du robot. Il centralise toutes les données
    de télémétrie (position, roues, capteurs, actionneurs, etc.) et permet
    de notifier l'interface graphique quand l'état change.

ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        RobotStateManager                            │
    │  (Gestionnaire principal - reçoit les données du robot)            │
    │                              │                                      │
    │                              ▼                                      │
    │                         RobotState                                  │
    │  (Contient toutes les données: position, roues, capteurs, etc.)   │
    │                              │                                      │
    │                              ▼                                      │
    │                    Interface Graphique                              │
    │  (Écoute les changements via le système de listeners)              │
    └─────────────────────────────────────────────────────────────────────┘

COMMENT AJOUTER UN NOUVEAU CAPTEUR:
    1. Ajouter un nouveau Sensor dans la liste 'sensors' de RobotState
    2. Utiliser state_manager.update_sensor(index, valeur) pour le mettre à jour

COMMENT AJOUTER UN NOUVEL ACTIONNEUR:
    1. Ajouter un nouveau Actuator dans la liste 'actuators' de RobotState
    2. Utiliser state_manager.update_actuator(index, position, is_enabled)

COMMENT AJOUTER UNE NOUVELLE DONNÉE:
    1. Ajouter l'attribut dans la classe RobotState
    2. L'ajouter dans la méthode to_dict() de RobotState
    3. Créer une méthode update_xxx() dans RobotStateManager
    4. Mettre à jour l'interface graphique pour l'afficher
"""

import time
import threading
import math
import random
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, List
from enum import Enum


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                              ÉNUMÉRATIONS                                    ║
# ║  Définissent les valeurs possibles pour certains états                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class WheelState(Enum):
    """
    États possibles pour une roue.
    
    POUR AJOUTER UN NOUVEL ÉTAT:
        Ajouter une nouvelle ligne: NOM_ETAT = "nom_etat"
    
    Exemple d'utilisation:
        wheel.state = WheelState.FORWARD.value
    """
    STOPPED = "stopped"      # Roue arrêtée
    FORWARD = "forward"      # Roue en marche avant
    BACKWARD = "backward"    # Roue en marche arrière


class RobotMode(Enum):
    """
    Modes de fonctionnement du robot.
    
    POUR AJOUTER UN NOUVEAU MODE:
        Ajouter une nouvelle ligne: NOM_MODE = "nom_mode"
    
    Exemple d'utilisation:
        state_manager.set_mode(RobotMode.AUTONOMOUS.value)
    """
    IDLE = "idle"                      # Robot en attente
    AUTONOMOUS = "autonomous"          # Mode autonome (match)
    MANUAL = "manual"                  # Contrôle manuel
    EMERGENCY_STOP = "emergency_stop"  # Arrêt d'urgence activé


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          CLASSES DE DONNÉES                                  ║
# ║  Structures pour stocker les différentes informations du robot               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@dataclass
class Position:
    """
    Position du robot sur le terrain Eurobot.
    
    Le terrain Eurobot fait 3000mm x 2000mm (3m x 2m).
    L'origine (0,0) est généralement dans un coin du terrain.
    
    Attributs:
        x (float): Position horizontale en millimètres (0 à 3000)
        y (float): Position verticale en millimètres (0 à 2000)
        theta (float): Orientation en degrés (0 à 360)
    
    POUR MODIFIER LES UNITÉS:
        Changer les commentaires et adapter le code qui utilise Position
    """
    x: float = 0.0      # Position X en mm
    y: float = 0.0      # Position Y en mm
    theta: float = 0.0  # Angle en degrés (0° = face à droite)


@dataclass
class Wheel:
    """
    Représente une roue du robot.
    
    Attributs:
        name (str): Nom de la roue (ex: "front_left")
        state (str): État actuel (voir WheelState)
        speed (float): Vitesse actuelle en RPM (tours par minute)
        target_speed (float): Vitesse cible demandée en RPM
        encoder_ticks (int): Compteur d'impulsions de l'encodeur
    
    POUR AJOUTER UNE DONNÉE À UNE ROUE:
        1. Ajouter l'attribut ici avec sa valeur par défaut
        2. Les données seront automatiquement incluses grâce à asdict()
    """
    name: str                                    # Nom identifiant la roue
    state: str = WheelState.STOPPED.value        # État actuel
    speed: float = 0.0                           # Vitesse actuelle (RPM)
    target_speed: float = 0.0                    # Vitesse cible (RPM)
    encoder_ticks: int = 0                       # Compteur encodeur


@dataclass
class Sensor:
    """
    Représente un capteur du robot.
    
    Attributs:
        name (str): Nom du capteur (ex: "lidar_front")
        value (float): Valeur lue par le capteur
        unit (str): Unité de mesure (ex: "mm", "cm", "")
        is_active (bool): Si le capteur est actif/fonctionnel
    
    POUR AJOUTER UN NOUVEAU TYPE DE CAPTEUR:
        Créer une nouvelle instance de Sensor dans RobotState.sensors
        Exemple: Sensor(name="temperature", unit="°C")
    """
    name: str                # Nom du capteur
    value: float = 0.0       # Valeur mesurée
    unit: str = ""           # Unité (mm, cm, °C, etc.)
    is_active: bool = True   # Capteur fonctionnel?


@dataclass
class Actuator:
    """
    Représente un actionneur du robot (bras, pince, etc.).
    
    Attributs:
        name (str): Nom de l'actionneur (ex: "gripper")
        position (float): Position actuelle (0-100%)
        is_enabled (bool): Si l'actionneur est activé
    
    POUR AJOUTER UN NOUVEL ACTIONNEUR:
        Créer une nouvelle instance dans RobotState.actuators
        Exemple: Actuator(name="cannon")
    """
    name: str                  # Nom de l'actionneur
    position: float = 0.0      # Position en pourcentage (0-100)
    is_enabled: bool = False   # Actionneur activé?


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                            ÉTAT DU ROBOT                                     ║
# ║  Classe principale contenant TOUTES les données du robot                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@dataclass
class RobotState:
    """
    État complet du robot pour Eurobot 2026.
    
    Cette classe contient TOUTES les informations sur l'état actuel du robot.
    Elle est mise à jour par RobotStateManager et lue par l'interface graphique.
    
    ═══════════════════════════════════════════════════════════════════════════
    POUR AJOUTER UNE NOUVELLE DONNÉE AU ROBOT:
    ═══════════════════════════════════════════════════════════════════════════
    
    1. Ajouter l'attribut dans cette classe:
       ma_nouvelle_donnee: float = 0.0
    
    2. L'ajouter dans la méthode to_dict():
       'ma_nouvelle_donnee': self.ma_nouvelle_donnee,
    
    3. Créer une méthode de mise à jour dans RobotStateManager:
       def update_ma_nouvelle_donnee(self, valeur):
           with self._lock:
               self._state.ma_nouvelle_donnee = valeur
               self._state.last_update = time.time()
           self._notify_listeners()
    
    4. Mettre à jour l'interface graphique (robot_interface.py) pour l'afficher
    ═══════════════════════════════════════════════════════════════════════════
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # INFORMATIONS GÉNÉRALES
    # ─────────────────────────────────────────────────────────────────────────
    robot_name: str = "Robot cool qui casse tout"  # Nom du robot
    team_name: str = "Pas encore ingénieur"        # Nom de l'équipe
    mode: str = RobotMode.IDLE.value               # Mode actuel (voir RobotMode)
    is_connected: bool = False                     # Connexion WiFi/Bluetooth OK?
    battery_level: float = 100.0                   # Niveau batterie (0-100%)
    match_time_remaining: int = 100                # Temps restant en secondes
    score: int = 0                                 # Score actuel du match
    
    # ─────────────────────────────────────────────────────────────────────────
    # POSITION ET MOUVEMENT
    # ─────────────────────────────────────────────────────────────────────────
    position: Position = field(default_factory=Position)           # Position actuelle
    target_position: Position = field(default_factory=Position)    # Position cible
    direction: float = 0.0           # Direction actuelle en degrés
    angular_velocity: float = 0.0    # Vitesse de rotation (deg/s)
    linear_velocity: float = 0.0     # Vitesse linéaire (mm/s)
    
    # ─────────────────────────────────────────────────────────────────────────
    # ROUES
    # Pour modifier les roues: changer cette liste
    # Par défaut: 4 roues (robot holonome ou différentiel à 4 roues)
    # ─────────────────────────────────────────────────────────────────────────
    wheels: List[Wheel] = field(default_factory=lambda: [
        Wheel(name="front_left"),    # Roue avant gauche
        Wheel(name="front_right"),   # Roue avant droite
        Wheel(name="rear_left"),     # Roue arrière gauche
        Wheel(name="rear_right"),    # Roue arrière droite
    ])
    
    # ─────────────────────────────────────────────────────────────────────────
    # CAPTEURS
    # POUR AJOUTER UN CAPTEUR: ajouter une ligne Sensor(name="...", unit="...")
    # ─────────────────────────────────────────────────────────────────────────
    sensors: List[Sensor] = field(default_factory=lambda: [
        # Capteurs de distance
        Sensor(name="lidar_front", unit="mm"),       # LiDAR avant
        Sensor(name="lidar_rear", unit="mm"),        # LiDAR arrière
        Sensor(name="ultrasonic_left", unit="mm"),   # Ultrason gauche
        Sensor(name="ultrasonic_right", unit="mm"),  # Ultrason droite
        # Capteurs de ligne (pour détecter les bords du terrain)
        Sensor(name="line_sensor_1", unit=""),       # Capteur ligne 1
        Sensor(name="line_sensor_2", unit=""),       # Capteur ligne 2
        Sensor(name="line_sensor_3", unit=""),       # Capteur ligne 3
        # AJOUTER VOS CAPTEURS ICI:
        # Sensor(name="mon_capteur", unit="unité"),
    ])
    
    # ─────────────────────────────────────────────────────────────────────────
    # ACTIONNEURS
    # POUR AJOUTER UN ACTIONNEUR: ajouter une ligne Actuator(name="...")
    # ─────────────────────────────────────────────────────────────────────────
    actuators: List[Actuator] = field(default_factory=lambda: [
        Actuator(name="gripper"),        # Pince
        Actuator(name="arm_elevation"),  # Élévation du bras
        Actuator(name="arm_rotation"),   # Rotation du bras
        Actuator(name="flag_deployer"),  # Déployeur de drapeau (fin de match)
        # AJOUTER VOS ACTIONNEURS ICI:
        # Actuator(name="mon_actionneur"),
    ])
    
    # ─────────────────────────────────────────────────────────────────────────
    # FLAGS DE STATUT
    # Indicateurs booléens pour différents états
    # ─────────────────────────────────────────────────────────────────────────
    obstacle_detected: bool = False        # Obstacle détecté devant?
    emergency_stop_active: bool = False    # Arrêt d'urgence activé?
    calibration_done: bool = False         # Calibration effectuée?
    aruco_detected: bool = False           # Marqueur ArUco détecté?
    detected_aruco_ids: List[int] = field(default_factory=list)  # IDs détectés
    
    # ─────────────────────────────────────────────────────────────────────────
    # HORODATAGE
    # ─────────────────────────────────────────────────────────────────────────
    last_update: float = field(default_factory=time.time)  # Dernière mise à jour
    
    def to_dict(self) -> dict:
        """
        Convertit l'état en dictionnaire Python.
        
        Utilisé pour:
        - Envoyer les données à l'interface graphique
        - Sauvegarder l'état
        - Déboguer
        
        IMPORTANT: Si vous ajoutez un nouvel attribut à RobotState,
                   vous DEVEZ l'ajouter ici aussi!
        
        Returns:
            dict: Dictionnaire contenant toutes les données de l'état
        """
        return {
            # Infos générales
            'robot_name': self.robot_name,
            'team_name': self.team_name,
            'mode': self.mode,
            'is_connected': self.is_connected,
            'battery_level': self.battery_level,
            'match_time_remaining': self.match_time_remaining,
            'score': self.score,
            # Position et mouvement
            'position': asdict(self.position),
            'target_position': asdict(self.target_position),
            'direction': self.direction,
            'angular_velocity': self.angular_velocity,
            'linear_velocity': self.linear_velocity,
            # Roues, capteurs, actionneurs (convertis automatiquement)
            'wheels': [asdict(w) for w in self.wheels],
            'sensors': [asdict(s) for s in self.sensors],
            'actuators': [asdict(a) for a in self.actuators],
            # Flags de statut
            'obstacle_detected': self.obstacle_detected,
            'emergency_stop_active': self.emergency_stop_active,
            'calibration_done': self.calibration_done,
            'aruco_detected': self.aruco_detected,
            'detected_aruco_ids': self.detected_aruco_ids,
            # Horodatage
            'last_update': self.last_update,
            # AJOUTER VOS NOUVELLES DONNÉES ICI:
            # 'ma_nouvelle_donnee': self.ma_nouvelle_donnee,
        }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        GESTIONNAIRE D'ÉTAT                                   ║
# ║  Classe qui gère les mises à jour et notifie l'interface                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class RobotStateManager:
    """
    Gestionnaire centralisé de l'état du robot.
    
    Cette classe est le POINT D'ENTRÉE pour:
    - Mettre à jour l'état du robot (depuis la communication WiFi/Bluetooth)
    - Lire l'état actuel
    - Être notifié des changements (pattern Observer)
    
    THREAD-SAFE: Peut être utilisé depuis plusieurs threads simultanément.
    
    ═══════════════════════════════════════════════════════════════════════════
    EXEMPLE D'UTILISATION:
    ═══════════════════════════════════════════════════════════════════════════
    
    # Créer le gestionnaire
    manager = RobotStateManager()
    
    # Ajouter un listener (sera appelé à chaque mise à jour)
    def on_state_change(state):
        print(f"Position: {state.position.x}, {state.position.y}")
    manager.add_listener(on_state_change)
    
    # Mettre à jour la position (depuis votre code de communication)
    manager.update_position(x=100, y=200, theta=45)
    
    # Lire l'état actuel
    state = manager.get_state()
    print(state.battery_level)
    
    ═══════════════════════════════════════════════════════════════════════════
    POUR AJOUTER UNE NOUVELLE MÉTHODE DE MISE À JOUR:
    ═══════════════════════════════════════════════════════════════════════════
    
    def update_ma_donnee(self, valeur: float):
        '''Met à jour ma_donnee'''
        with self._lock:  # IMPORTANT: toujours utiliser le lock!
            self._state.ma_donnee = valeur
            self._state.last_update = time.time()
        self._notify_listeners()  # Notifier l'interface
    
    ═══════════════════════════════════════════════════════════════════════════
    """
    
    def __init__(self):
        """Initialise le gestionnaire avec un état par défaut."""
        self._state = RobotState()                              # État du robot
        self._lock = threading.Lock()                           # Verrou thread-safe
        self._listeners: List[Callable[[RobotState], None]] = []  # Callbacks
        self._running = False                                   # Simulation active?
        self._simulation_thread: Optional[threading.Thread] = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # LECTURE DE L'ÉTAT
    # ─────────────────────────────────────────────────────────────────────────
    
    @property
    def state(self) -> RobotState:
        """
        Accède à l'état actuel (lecture seule recommandée).
        
        Exemple:
            manager = RobotStateManager()
            print(manager.state.position.x)
        """
        with self._lock:
            return self._state
    
    def get_state(self) -> RobotState:
        """
        Retourne l'état actuel du robot.
        
        Returns:
            RobotState: L'état complet du robot
        """
        with self._lock:
            return self._state
    
    # ─────────────────────────────────────────────────────────────────────────
    # SYSTÈME DE LISTENERS (OBSERVATEURS)
    # Permet à l'interface d'être notifiée des changements
    # ─────────────────────────────────────────────────────────────────────────
    
    def add_listener(self, callback: Callable[[RobotState], None]):
        """
        Ajoute un listener qui sera appelé à chaque mise à jour.
        
        Le callback reçoit l'état complet du robot en paramètre.
        
        Args:
            callback: Fonction qui prend un RobotState en paramètre
        
        Exemple:
            def mon_callback(state):
                print(f"Batterie: {state.battery_level}%")
            manager.add_listener(mon_callback)
        """
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[RobotState], None]):
        """
        Supprime un listener précédemment ajouté.
        
        Args:
            callback: Le callback à supprimer
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self):
        """
        Notifie tous les listeners qu'un changement a eu lieu.
        
        Appelé automatiquement par toutes les méthodes update_xxx().
        Vous n'avez normalement pas besoin d'appeler cette méthode directement.
        """
        for listener in self._listeners:
            try:
                listener(self._state)
            except Exception as e:
                print(f"[ERREUR] Erreur lors de la notification du listener: {e}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTHODES DE MISE À JOUR DE L'ÉTAT
    # Utilisez ces méthodes depuis votre code de communication robot
    # ─────────────────────────────────────────────────────────────────────────
    
    def update_position(self, x: float, y: float, theta: float):
        """
        Met à jour la position du robot.
        
        Args:
            x: Position X en millimètres (0-3000 sur terrain Eurobot)
            y: Position Y en millimètres (0-2000 sur terrain Eurobot)
            theta: Orientation en degrés (0-360)
        
        Exemple:
            # Depuis votre code de communication:
            manager.update_position(x=1500, y=1000, theta=90)
        """
        with self._lock:
            self._state.position.x = x
            self._state.position.y = y
            self._state.position.theta = theta
            self._state.direction = theta
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def update_wheel(self, wheel_index: int, state: str = None, speed: float = None):
        """
        Met à jour l'état d'une roue.
        
        Args:
            wheel_index: Index de la roue (0=front_left, 1=front_right, etc.)
            state: Nouvel état (optionnel) - utiliser WheelState.XXX.value
            speed: Nouvelle vitesse en RPM (optionnel)
        
        Exemple:
            # Roue avant gauche en marche avant à 60 RPM
            manager.update_wheel(0, state=WheelState.FORWARD.value, speed=60)
        """
        with self._lock:
            if 0 <= wheel_index < len(self._state.wheels):
                if state is not None:
                    self._state.wheels[wheel_index].state = state
                if speed is not None:
                    self._state.wheels[wheel_index].speed = speed
                self._state.last_update = time.time()
        self._notify_listeners()
    
    def update_sensor(self, sensor_index: int, value: float):
        """
        Met à jour la valeur d'un capteur.
        
        Args:
            sensor_index: Index du capteur dans la liste sensors
            value: Nouvelle valeur mesurée
        
        Exemple:
            # Mettre à jour le LiDAR avant (index 0) avec 150mm
            manager.update_sensor(0, 150.0)
        """
        with self._lock:
            if 0 <= sensor_index < len(self._state.sensors):
                self._state.sensors[sensor_index].value = value
                self._state.last_update = time.time()
        self._notify_listeners()
    
    def update_actuator(self, actuator_index: int, position: float = None, 
                        is_enabled: bool = None):
        """
        Met à jour l'état d'un actionneur.
        
        Args:
            actuator_index: Index de l'actionneur
            position: Position en pourcentage 0-100 (optionnel)
            is_enabled: Si l'actionneur est activé (optionnel)
        
        Exemple:
            # Ouvrir la pince à 75%
            manager.update_actuator(0, position=75.0, is_enabled=True)
        """
        with self._lock:
            if 0 <= actuator_index < len(self._state.actuators):
                if position is not None:
                    self._state.actuators[actuator_index].position = position
                if is_enabled is not None:
                    self._state.actuators[actuator_index].is_enabled = is_enabled
                self._state.last_update = time.time()
        self._notify_listeners()
    
    def set_mode(self, mode: str):
        """
        Change le mode de fonctionnement du robot.
        
        Args:
            mode: Le nouveau mode (utiliser RobotMode.XXX.value)
        
        Exemple:
            manager.set_mode(RobotMode.AUTONOMOUS.value)
        """
        with self._lock:
            self._state.mode = mode
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def set_connected(self, connected: bool):
        """
        Met à jour le statut de connexion.
        
        Args:
            connected: True si connecté au robot, False sinon
        """
        with self._lock:
            self._state.is_connected = connected
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def set_battery_level(self, level: float):
        """
        Met à jour le niveau de batterie.
        
        Args:
            level: Niveau en pourcentage (0-100)
        """
        with self._lock:
            self._state.battery_level = max(0.0, min(100.0, level))
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def set_emergency_stop(self, active: bool):
        """
        Active ou désactive l'arrêt d'urgence.
        
        Quand activé:
        - Le mode passe en EMERGENCY_STOP
        - Toutes les roues sont arrêtées
        
        Args:
            active: True pour activer l'arrêt d'urgence
        """
        with self._lock:
            self._state.emergency_stop_active = active
            if active:
                self._state.mode = RobotMode.EMERGENCY_STOP.value
                # Arrêter toutes les roues
                for wheel in self._state.wheels:
                    wheel.state = WheelState.STOPPED.value
                    wheel.speed = 0.0
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def update_aruco_detection(self, detected: bool, ids: List[int] = None):
        """
        Met à jour la détection de marqueurs ArUco.
        
        Args:
            detected: True si des marqueurs sont détectés
            ids: Liste des IDs détectés (optionnel)
        
        Exemple:
            # ArUco ID 23 et 42 détectés
            manager.update_aruco_detection(True, [23, 42])
        """
        with self._lock:
            self._state.aruco_detected = detected
            self._state.detected_aruco_ids = ids if ids else []
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def update_match_time(self, time_remaining: int):
        """
        Met à jour le temps restant du match.
        
        Args:
            time_remaining: Temps restant en secondes (0-100)
        """
        with self._lock:
            self._state.match_time_remaining = max(0, time_remaining)
            self._state.last_update = time.time()
        self._notify_listeners()
    
    def update_score(self, score: int):
        """
        Met à jour le score actuel.
        
        Args:
            score: Nouveau score
        """
        with self._lock:
            self._state.score = score
            self._state.last_update = time.time()
        self._notify_listeners()
    
    # ─────────────────────────────────────────────────────────────────────────
    # MODE SIMULATION
    # Génère des données fictives pour tester l'interface sans robot réel
    # ─────────────────────────────────────────────────────────────────────────
    
    def start_simulation(self):
        """
        Démarre le mode simulation.
        
        Génère des données fictives pour tester l'interface sans robot.
        Le robot simulé:
        - Se déplace en cercle sur le terrain
        - A des vitesses variables
        - Détecte parfois des ArUco
        - Vide lentement sa batterie
        
        Pour l'arrêter: manager.stop_simulation()
        """
        self._running = True
        
        def simulation_loop():
            """Boucle de simulation - génère des données fictives."""
            t = 0
            while self._running:
                with self._lock:
                    # ─────────────────────────────────────────────────────────
                    # Simulation du mouvement (cercle)
                    # Modifiez ces formules pour changer le comportement
                    # ─────────────────────────────────────────────────────────
                    self._state.position.x = 1500 + 500 * math.sin(t * 0.1)
                    self._state.position.y = 1000 + 400 * math.cos(t * 0.1)
                    self._state.position.theta = (t * 10) % 360
                    self._state.direction = self._state.position.theta
                    
                    # Simulation des vitesses
                    self._state.linear_velocity = 100 + random.uniform(-10, 10)
                    self._state.angular_velocity = 5 + random.uniform(-2, 2)
                    
                    # ─────────────────────────────────────────────────────────
                    # Simulation des roues
                    # ─────────────────────────────────────────────────────────
                    for wheel in self._state.wheels:
                        wheel.state = WheelState.FORWARD.value
                        wheel.speed = 60 + random.uniform(-5, 5)
                        wheel.encoder_ticks += int(wheel.speed)
                    
                    # ─────────────────────────────────────────────────────────
                    # Simulation des capteurs
                    # ─────────────────────────────────────────────────────────
                    for sensor in self._state.sensors:
                        if "lidar" in sensor.name or "ultrasonic" in sensor.name:
                            # Capteurs de distance: valeurs entre 150 et 250 mm
                            sensor.value = 200 + random.uniform(-50, 50)
                        else:
                            # Capteurs de ligne: 0 ou 1
                            sensor.value = random.choice([0, 1])
                    
                    # ─────────────────────────────────────────────────────────
                    # Simulation batterie et détection
                    # ─────────────────────────────────────────────────────────
                    # La batterie descend jusqu'à 20% puis remonte (simulation cyclique)
                    if self._state.battery_level <= 20:
                        self._state.battery_level = 100.0  # Reset batterie
                    else:
                        self._state.battery_level -= 0.05
                    
                    # ArUco détecté aléatoirement (70% du temps)
                    self._state.aruco_detected = random.random() > 0.3
                    if self._state.aruco_detected:
                        self._state.detected_aruco_ids = [23]
                    else:
                        self._state.detected_aruco_ids = []
                    
                    self._state.is_connected = True
                    self._state.mode = RobotMode.AUTONOMOUS.value
                    self._state.last_update = time.time()
                
                self._notify_listeners()
                t += 1
                time.sleep(0.1)  # Mise à jour toutes les 100ms (10 Hz)
        
        self._simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        self._simulation_thread.start()
        print("[INFO] Mode simulation démarré")
    
    def stop_simulation(self):
        """Arrête le mode simulation."""
        self._running = False
        if self._simulation_thread:
            self._simulation_thread.join(timeout=1.0)
            self._simulation_thread = None
        print("[INFO] Mode simulation arrêté")
