"""
automate.py - Séquences de mouvements automatiques pour le robot

Ce script tourne sur le Raspberry Pi.
Connexion : ssh admin@<IP_DU_PI> puis python automate.py

Modifie la fonction sequence() pour définir ta séquence de mouvements.
"""

import serial
import time
import sys

# ── Configuration ────────────────────────────────────────────────────────────
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE   = 9600
# ─────────────────────────────────────────────────────────────────────────────


def connect_arduino():
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"Arduino connecté sur {SERIAL_PORT}")
        return arduino
    except serial.SerialException as e:
        print(f"Erreur : {e}")
        sys.exit(1)


def cmd(arduino, commande, pause=0.0):
    """Envoie une commande et attend optionnellement avant la suivante."""
    arduino.write((commande + "\n").encode())
    response = arduino.readline().decode().strip()
    print(f"  {commande}  →  {response}")
    if pause > 0:
        time.sleep(pause)


def avancer(arduino, duree, vitesse=200):
    cmd(arduino, f"MOVE forward {vitesse}")
    time.sleep(duree)
    cmd(arduino, "MOVE stop 0")

def reculer(arduino, duree, vitesse=200):
    cmd(arduino, f"MOVE backward {vitesse}")
    time.sleep(duree)
    cmd(arduino, "MOVE stop 0")

def tourner_gauche(arduino, duree, vitesse=150):
    cmd(arduino, f"MOVE rotateCCW {vitesse}")
    time.sleep(duree)
    cmd(arduino, "MOVE stop 0")

def tourner_droite(arduino, duree, vitesse=150):
    cmd(arduino, f"MOVE rotateCW {vitesse}")
    time.sleep(duree)
    cmd(arduino, "MOVE stop 0")

def aller_gauche(arduino, duree, vitesse=200):
    cmd(arduino, f"MOVE left {vitesse}")
    time.sleep(duree)
    cmd(arduino, "MOVE stop 0")

def aller_droite(arduino, duree, vitesse=200):
    cmd(arduino, f"MOVE right {vitesse}")
    time.sleep(duree)
    cmd(arduino, "MOVE stop 0")

def ouvrir_pince(arduino):
    cmd(arduino, "ClampRelease", pause=0.5)

def fermer_pince(arduino):
    cmd(arduino, "ClampGrab", pause=0.5)

def monter_bras(arduino):
    cmd(arduino, "ClampUp", pause=0.5)

def descendre_bras(arduino):
    cmd(arduino, "ClampDown", pause=0.5)

def stop(arduino):
    cmd(arduino, "MOVE stop 0")


# ═══════════════════════════════════════════════════════════════
#  ↓↓↓  MODIFIE ICI TA SÉQUENCE  ↓↓↓
# ═══════════════════════════════════════════════════════════════

def sequence(arduino):
    """Séquence de mouvements à exécuter automatiquement."""

    print("\n--- Début de la séquence ---\n")

    avancer(arduino, duree=2.0, vitesse=200)    # Avancer pendant 2 secondes
    tourner_droite(arduino, duree=0.8)          # Tourner à droite ~90°
    avancer(arduino, duree=1.5)                 # Avancer encore
    descendre_bras(arduino)                     # Descendre le bras
    fermer_pince(arduino)                       # Attraper quelque chose
    monter_bras(arduino)                        # Lever le bras
    reculer(arduino, duree=1.0)                 # Reculer
    tourner_gauche(arduino, duree=0.8)          # Revenir face à l'autre sens
    avancer(arduino, duree=2.0)                 # Aller déposer
    descendre_bras(arduino)
    ouvrir_pince(arduino)                       # Lâcher
    monter_bras(arduino)

    print("\n--- Séquence terminée ---\n")


# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    arduino = connect_arduino()
    try:
        sequence(arduino)
    except KeyboardInterrupt:
        print("\nInterrompu par Ctrl+C")
    finally:
        stop(arduino)
        arduino.close()
        print("Déconnecté.")
