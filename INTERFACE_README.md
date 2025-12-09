# 🤖 Interface Robot - Guide d'utilisation

## Eurobot 2026 - Équipe "Pas encore ingénieur"

Ce guide explique comment utiliser et personnaliser l'interface graphique du robot.

---

## 📋 Table des matières

1. [Installation](#installation)
2. [Lancement rapide](#lancement-rapide)
3. [Structure des fichiers](#structure-des-fichiers)
4. [Comment personnaliser l'interface](#comment-personnaliser-linterface)
5. [Intégration avec le robot](#intégration-avec-le-robot)
6. [FAQ et Dépannage](#faq-et-dépannage)

---

## 🔧 Installation

### Prérequis
- Python 3.10 ou supérieur
- Tkinter (normalement inclus avec Python)

### Installation des dépendances

```bash
# Installer toutes les dépendances
pip install -r requirements.txt
```

---

## 🚀 Lancement rapide

### Mode simulation (pour tester sans robot)
```bash
python main.py --simulation
# ou
python main.py -s
```

### Mode normal (avec robot réel)
```bash
python main.py
```

### Afficher l'aide
```bash
python main.py --help
```

---

## 📁 Structure des fichiers

```
robot-cool-qui-casse-tout/
│
├── main.py                 # Point d'entrée - LANCER CE FICHIER
│   │
│   └── Que fait-il ?
│       - Analyse les arguments (--simulation, etc.)
│       - Crée le RobotStateManager
│       - Lance l'interface graphique
│
├── robot_state.py          # Gestion de l'état du robot
│   │
│   └── Classes importantes:
│       - RobotState: Contient TOUTES les données du robot
│       - RobotStateManager: Gère les mises à jour
│       - WheelState: États possibles des roues
│       - RobotMode: Modes de fonctionnement
│
├── robot_interface.py      # Interface graphique (Tkinter)
│   │
│   └── Classe principale:
│       - RobotInterface: Crée et gère la fenêtre
│       - Méthodes _create_*: Créent les panneaux
│       - Méthodes _update_*: Mettent à jour l'affichage
│
├── requirements.txt        # Dépendances Python
├── INTERFACE_README.md     # CE FICHIER
│
└── (autres fichiers existants: calibration.py, pos_estimation.py, etc.)
```

---

## 🎨 Comment personnaliser l'interface

### 1. Ajouter un nouveau capteur

**Étape 1:** Ouvrir `robot_state.py`, trouver la section `sensors`:

```python
sensors: List[Sensor] = field(default_factory=lambda: [
    Sensor(name="lidar_front", unit="mm"),
    # ... autres capteurs ...
    
    # AJOUTER VOTRE CAPTEUR ICI:
    Sensor(name="mon_nouveau_capteur", unit="°C"),
])
```

**Étape 2:** Ouvrir `robot_interface.py`, trouver `sensor_display_names`:

```python
sensor_display_names = {
    # ... existants ...
    "mon_nouveau_capteur": "Mon Capteur",  # AJOUTER ICI
}
```

**C'est tout!** L'interface affichera automatiquement le nouveau capteur.

---

### 2. Ajouter un nouvel actionneur

**Étape 1:** Dans `robot_state.py`, section `actuators`:

```python
actuators: List[Actuator] = field(default_factory=lambda: [
    # ... existants ...
    
    # AJOUTER ICI:
    Actuator(name="canon"),
])
```

**Étape 2:** Dans `robot_interface.py`, `actuator_display_names`:

```python
actuator_display_names = {
    # ... existants ...
    "canon": "Canon à balles",  # AJOUTER ICI
}
```

---

### 3. Changer les couleurs

Ouvrir `robot_interface.py`, modifier le dictionnaire `COLORS`:

```python
COLORS = {
    'background': '#1a1a2e',     # Fond principal
    'panel_bg': '#16213e',       # Fond des panneaux
    'robot_body': '#ff6b6b',     # Couleur du robot
    # ... modifier les couleurs que vous voulez ...
}
```

---

### 4. Modifier le terrain

Ouvrir `robot_interface.py`, modifier les constantes:

```python
# Dimensions réelles du terrain (en mm)
TERRAIN_REAL_WIDTH = 3000   # Largeur
TERRAIN_REAL_HEIGHT = 2000  # Hauteur

# Dimensions affichées (en pixels)
TERRAIN_DISPLAY_WIDTH = 450
TERRAIN_DISPLAY_HEIGHT = 300
```

---

### 5. Ajouter un nouveau panneau d'information

**Étape 1:** Créer la méthode dans `robot_interface.py`:

```python
def _create_mon_panneau(self):
    """Crée mon nouveau panneau."""
    panel = self._create_panel("🆕 Mon Panneau")
    
    # Ajouter des éléments
    row = tk.Frame(panel, bg=COLORS['panel_bg'])
    row.pack(fill=tk.X, pady=5)
    
    self.mon_label = tk.Label(
        row, text="Ma valeur: 0",
        font=("Arial", 12),
        fg=COLORS['text_primary'],
        bg=COLORS['panel_bg']
    )
    self.mon_label.pack()
```

**Étape 2:** Appeler la méthode dans `_create_main_content()`:

```python
# Créer les panneaux d'information
self._create_position_panel()
# ... autres panneaux ...
self._create_mon_panneau()  # AJOUTER ICI
```

**Étape 3:** Mettre à jour dans `_update_display()`:

```python
def _update_mon_panneau(self, state):
    self.mon_label.config(text=f"Ma valeur: {state.ma_valeur}")
```

---

### 6. Ajouter un bouton

Dans `_create_control_buttons()`:

```python
mon_bouton = tk.Button(
    self.button_frame,
    text="🎯 Mon Action",
    font=("Arial", 10),
    command=self._on_mon_action
)
mon_bouton.pack(side=tk.LEFT, padx=5)

# Et créer le callback:
def _on_mon_action(self):
    """Appelé quand on clique sur le bouton."""
    print("Action!")
    # Votre code ici
```

---

## 🔌 Intégration avec le robot

### Architecture de communication

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     ROBOT       │  WiFi/  │       PC        │         │   INTERFACE     │
│   (Raspberry    │ ─────── │  (Ce code)      │ ─────── │   (Tkinter)     │
│    Pi, etc.)    │  BT     │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                            
                            RobotStateManager
                            reçoit les données
                            et notifie l'interface
```

### Exemple de code d'intégration

```python
import threading
from robot_state import RobotStateManager
from robot_interface import RobotInterface

# 1. Créer le gestionnaire
manager = RobotStateManager()

# Variable pour contrôler l'arrêt propre
running = True

# 2. Thread de communication (à adapter selon votre protocole)
def communication_thread():
    import socket
    
    # Configuration avec timeout pour éviter les blocages
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)  # Timeout de 5 secondes
    
    try:
        sock.connect(('192.168.1.100', 5000))  # IP du robot
    except socket.error as e:
        print(f"Erreur de connexion: {e}")
        manager.set_connected(False)
        return
    
    while running:
        try:
            # Recevoir les données
            data = sock.recv(1024)
            if not data:
                break
            
            # Parser les données (format à définir)
            # Par exemple JSON:
            import json
            robot_data = json.loads(data.decode())
            
            # Mettre à jour l'interface
            manager.update_position(
                x=robot_data['x'],
                y=robot_data['y'],
                theta=robot_data['theta']
            )
            manager.set_battery_level(robot_data['battery'])
            manager.set_connected(True)
            
            # etc...
        except socket.timeout:
            continue  # Réessayer
        except Exception as e:
            print(f"Erreur: {e}")
            manager.set_connected(False)
            break
    
    sock.close()

# 3. Lancer le thread de communication
comm_thread = threading.Thread(target=communication_thread, daemon=True)
comm_thread.start()

# 4. Lancer l'interface (bloque jusqu'à fermeture)
interface = RobotInterface(manager)
interface.run()
```

### Méthodes disponibles pour mettre à jour l'état

```python
# Position
manager.update_position(x=1500, y=1000, theta=45)

# Roues
manager.update_wheel(0, state="forward", speed=60)  # Index 0 = front_left

# Capteurs
manager.update_sensor(0, 200)  # Index 0 = lidar_front

# Actionneurs
manager.update_actuator(0, position=75.0, is_enabled=True)  # Index 0 = gripper

# Statuts
manager.set_mode("autonomous")
manager.set_connected(True)
manager.set_battery_level(85)
manager.set_emergency_stop(False)

# Match
manager.update_match_time(75)
manager.update_score(42)

# ArUco
manager.update_aruco_detection(True, [23, 42])
```

---

## ❓ FAQ et Dépannage

### L'interface ne s'ouvre pas

**Vérifiez que Tkinter est installé:**
```bash
python -c "import tkinter; print('OK')"
```

Si erreur, installez Tkinter:
- **Ubuntu/Debian:** `sudo apt-get install python3-tk`
- **Fedora:** `sudo dnf install python3-tkinter`
- **Windows/Mac:** Normalement inclus avec Python

### Les données ne se mettent pas à jour

Vérifiez que vous appelez bien les méthodes `update_*` du `RobotStateManager`.

### Je veux changer la fréquence de mise à jour

Dans `robot_interface.py`, modifier:
```python
UPDATE_INTERVAL_MS = 100  # 100ms = 10 Hz
```

### Comment déboguer?

Ajoutez des prints dans `_on_state_update()`:
```python
def _on_state_update(self, state):
    print(f"DEBUG: Position = {state.position.x}, {state.position.y}")
    self._last_state = state
```

---

## 📞 Contact

Pour toute question sur le code, consultez les commentaires détaillés dans chaque fichier!

**Équipe: Pas encore ingénieur**
- Hugo Demont
- Morgan Martin  
- Damien Deteve

*Bonne compétition Eurobot 2026!* 🤖🏆
