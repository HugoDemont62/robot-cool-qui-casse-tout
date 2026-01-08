# Eurobot 2026 — Robot Control Python

[![wakatime](https://wakatime.com/badge/user/14fe3c61-8f4f-4dd2-b75c-eff28a472911/project/97255df1-cb63-4d77-9c1b-7cfa4b3b42ca.svg)](https://wakatime.com/badge/user/14fe3c61-8f4f-4dd2-b75c-eff28a472911/project/97255df1-cb63-4d77-9c1b-7cfa4b3b42ca)
[![Team](https://img.shields.io/badge/Team-Pas%20encore%20ing%C3%A9nieur-blue)]()
[![Robot](https://img.shields.io/badge/Robot-Robot%20cool%20qui%20casse%20tout-red)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)]()
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Status](https://img.shields.io/badge/Status-In%20development-orange)]()

---

Bienvenue sur le dépôt du projet **Eurobot 2026** — contrôle et supervision du robot « Robot cool qui casse tout ». Ce README a pour but d'être une documentation complète pour : installation, usage, déploiement et démonstration.

---

## Sommaire

- [Résumé](#résumé)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture et description des fichiers](#architecture-et-description-des-fichiers)
- [Déploiement et exécution sur le robot](#déploiement-et-exécution-sur-le-robot)
- [Licence](#licence)
- [Checklist - fichiers à ajouter/vérifier](#checklist---fichiers-à-ajoutervérifier)
- [Propositions d'améliorations additionnelles](#propositions-daméliorations-additionnelles)
- [Besoin d'aide pour la suite](#besoin-daide-pour-la-suite)

---

## Résumé

Ce projet fournit un ensemble d'outils Python pour piloter, surveiller et tester un robot destiné à la compétition Eurobot. Il inclut :

- Une interface graphique (Tkinter) pour visualiser l'état du robot et piloter manuellement.
- Modules de calibration et d'estimation de position (ArUco / OpenCV).
- Connectivité via SSH/paramiko vers le robot et sketch Arduino pour l'électronique embarquée.
- Outils de simulation et de logging pour le développement hors cible matériel.

[Regarder la démo vidéo](video/robot_demo.mp4)

---

## Installation

### Prérequis

Python 3.10+ et pip.

### Exemple d'installation (Windows / PowerShell)

```powershell
# Cloner le dépôt
git clone https://github.com/HugoDemont62/robot-cool-qui-casse-tout.git
cd robot-cool-qui-casse-tout

# Créer un venv et l'activer (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

**Note :** Si tu utilises Linux/macOS, la commande d'activation du venv est différente (`source .venv/bin/activate`).

### Dépendances principales

Les dépendances sont listées dans `requirements.txt`. Extraits importants :

- `opencv-contrib-python` (vision et ArUco)
- `opencv-python`
- `numpy`, `scipy` (calculs scientifiques)
- `ttkbootstrap` (thème/GUI)
- `paramiko` (SSH vers le robot)

Si tu rencontres des problèmes d'installation avec opencv, privilégie une roue binaire adaptée à ton OS et Python, ou installe via conda si nécessaire.

---

## Usage

### Lancement de l'interface

Mode simulation recommandé pour commencer :

```bash
# Mode simulation (aucun robot requis)
python main.py --simulation

# Mode normal (connexion au robot)
python main.py
```

### Exemples d'utilitaires

- `calibration.py` — outils pour calibrer la caméra et générer la matrice de calibration.
- `pos_estimation.py` — Utilise ArUco pour estimer la position et l'orientation du robot.
- `control_robot.py` — logique de haut niveau pour commandes de déplacement autonomes.
- `robot_ssh.py` — gestion de la connexion SSH et envoi de commandes au robot via `paramiko`.

### Exemple d'appel scripté (non interactif)

```bash
# Lancer une estimation de position et sauvegarder les résultats
python pos_estimation.py --input samples/frame.jpg --output out/pose.json
```

---

## Architecture et description des fichiers

### Arborescence principale et rôle des fichiers clés

- `main.py` : point d'entrée de l'interface et du mode simulation.
- `robot_interface.py` : implémentation Tkinter de l'interface graphique (widgets, vues terrain, contrôles).
- `robot_state.py` : modèle d'état du robot (position, capteurs, actionneurs, logs).
- `calibration.py` : scripts/utilitaires pour calibrer la caméra (OpenCV).
- `pos_estimation.py` : estimation de position via ArUco / OpenCV.
- `control_robot.py` : algorithmes de commande (PID, trajectoire, sécurité).
- `robot_ssh.py` : wrapper SSH (paramiko) pour déployer des scripts sur la carte du robot.
- `PEI_-_Code_Arduino.ino` : sketch Arduino utilisé pour l'électronique embarquée.
- `requirements.txt` : dépendances Python.
- `INTERFACE_README.md` : documentation détaillée de l'interface graphique.
- `tests/` : tests unitaires et mocks (ex : `tests/test_mocks.py`).

---

## Déploiement et exécution sur le robot

### 1) Déploiement via SSH

Exposé dans `robot_ssh.py` :

```bash
# Vérifier la connexion SSH
python robot_ssh.py --test-connection --host $ROBOT_HOST

# Transférer scripts : scp / paramiko utilities intégrées
```

### 2) Arduino

Le fichier `PEI_-_Code_Arduino.ino` contient le sketch; téléverse via l'IDE Arduino ou `arduino-cli`.

**Sécurité :** Assure-toi que la connexion SSH est protégée (clé SSH, pas de mots de passe en clair dans le dépôt).

---

## Licence

Ce projet est sous licence Creative Commons BY-NC 4.0 (voir `LICENSE.md`).