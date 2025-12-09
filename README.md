# Eurobot 2026 - Robot Control Python

[![Team](https://img.shields.io/badge/Team-Pas%20encore%20ing%C3%A9nieur-blue)]()
[![Robot](https://img.shields.io/badge/Robot-Robot%20cool%20qui%20casse%20tout-red)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)]()
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Status](https://img.shields.io/badge/Status-In%20development-orange)]()

---

Bienvenue sur le dépôt du projet **Eurobot 2026**, dédié au contrôle du robot  
**« Robot cool qui casse tout »**.  
Ce projet est développé en Python et permet de piloter le robot, gérer ses mouvements et ses interactions avec l’environnement du plateau.

---

## 👥 Équipe : **Pas encore ingénieur**

- **Hugo Demont** – Pas Ingénieur

- **Morgan Martin** – Pas Ingénieur

- **Damien Deteve** – Pas Ingénieur


---

## 🎯 Objectifs du projet

- Contrôle **précis** des déplacements du robot  
- Gestion des **capteurs & actionneurs**  
- Système **modulaire** pour tester plusieurs stratégies  
- Environnement de test & simulation  
- Robustesse & sécurité pour la compétition Eurobot

---

## ⚙️ Fonctionnalités principales

- Déplacements : avancer, reculer, tourner  
- Contrôle des moteurs & actionneurs  
- Lecture et analyse des capteurs  
- Simulation des trajectoires  
- Logging détaillé des actions
- **Interface graphique** pour visualiser l'état du robot en temps réel

---

## 🖥️ Interface Graphique

Une interface graphique complète en **Python (Tkinter)** permet de visualiser toutes les statistiques du robot en temps réel.

### Lancement rapide

```bash
# Mode simulation (pour tester sans robot)
python main.py --simulation

# Mode normal (avec robot réel via WiFi/Bluetooth)
python main.py
```

### Fonctionnalités de l'interface

- 📍 **Position du robot** sur le terrain (vue graphique)
- 🧭 **Direction** et orientation en temps réel
- 🔧 **État des roues** (vitesse, direction, encodeurs)
- 📡 **Capteurs** (LiDAR, ultrasons, capteurs de ligne)
- 🦾 **Actionneurs** (pince, bras, déployeur de drapeau)
- 🔋 **Batterie** et statut de connexion
- ⏱️ **Temps de match** et score
- 🎯 **Détection ArUco**
- 🛑 **Bouton d'arrêt d'urgence**

### Documentation complète

Consultez le fichier [INTERFACE_README.md](INTERFACE_README.md) pour :
- Personnaliser l'interface (ajouter capteurs, actionneurs, panneaux)
- Intégrer avec votre code de communication robot
- Modifier les couleurs et l'apparence

---

## 📁 Structure des fichiers

```
robot-cool-qui-casse-tout/
├── main.py                 # Point d'entrée de l'interface
├── robot_state.py          # Gestion de l'état du robot
├── robot_interface.py      # Interface graphique (Tkinter)
├── calibration.py          # Calibration caméra
├── pos_estimation.py       # Estimation position ArUco
├── requirements.txt        # Dépendances Python
├── INTERFACE_README.md     # Documentation de l'interface
└── README.md               # Ce fichier
```

---

## 🔧 Installation

```bash
# Cloner le dépôt
git clone https://github.com/HugoDemont62/robot-cool-qui-casse-tout.git
cd robot-cool-qui-casse-tout

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'interface
python main.py --simulation
```
