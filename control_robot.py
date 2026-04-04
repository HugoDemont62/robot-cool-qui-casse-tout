"""
control_robot.py - Pilotage clavier du robot via l'Arduino

Ce script tourne sur le Raspberry Pi.
Connexion : ssh admin@<IP_DU_PI> puis python control_robot.py

Contrôles :
  Z / Flèche haut    → Avancer
  S / Flèche bas     → Reculer
  Q / Flèche gauche  → Aller à gauche (strafe)
  D / Flèche droite  → Aller à droite (strafe)
  A                  → Rotation gauche
  E                  → Rotation droite
  Y / U / I / O      → Diagonales (avant-gauche / avant-droite / arrière-gauche / arrière-droite)
  Espace             → STOP
  + / -              → Augmenter / diminuer la vitesse
  ESC ou Ctrl+C      → Quitter
"""

import serial
import time
import sys

# ── Configuration ────────────────────────────────────────────────────────────
SERIAL_PORT = '/dev/ttyACM0'   # Port série de l'Arduino sur le Pi
BAUD_RATE   = 9600
SPEED       = 200              # Vitesse initiale (0-255)
SPEED_STEP  = 20               # Pas de changement de vitesse
# ─────────────────────────────────────────────────────────────────────────────


def connect_arduino(port=SERIAL_PORT, baud=BAUD_RATE):
    """Ouvre la connexion série avec l'Arduino. Quitte si échec."""
    try:
        arduino = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Attendre le reset de l'Arduino
        print(f"Arduino connecté sur {port}")
        return arduino
    except serial.SerialException as e:
        print(f"Erreur : impossible d'ouvrir {port} : {e}")
        print("Vérifiez que l'Arduino est branché et que le port est correct.")
        sys.exit(1)


def send(arduino, cmd):
    """Envoie une commande à l'Arduino et affiche la réponse."""
    arduino.write((cmd + "\n").encode())
    response = arduino.readline().decode().strip()
    print(f"  > {cmd}  →  {response}")
    return response


def run(arduino):
    """Boucle principale de contrôle clavier (mode curses interactif)."""
    import curses

    speed = SPEED

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)

    def draw():
        stdscr.clear()
        stdscr.addstr(0, 0, "═══════════════════════════════════")
        stdscr.addstr(1, 0, "  🤖  PILOTAGE ROBOT  (ESC = quitter)")
        stdscr.addstr(2, 0, "═══════════════════════════════════")
        stdscr.addstr(3, 0, "  Z/↑ Avancer    S/↓ Reculer")
        stdscr.addstr(4, 0, "  Q/← Gauche     D/→ Droite")
        stdscr.addstr(5, 0, "  A Rot.Gauche   E Rot.Droite")
        stdscr.addstr(6, 0, "  Y/U/I/O Diagonales   Espace STOP")
        stdscr.addstr(7, 0, "  + Vitesse+     - Vitesse-")
        stdscr.addstr(8, 0, "───────────────────────────────────")
        stdscr.addstr(9, 0, f"  Vitesse actuelle : {speed}")
        stdscr.refresh()

    draw()

    try:
        while True:
            keys = set()
            while True:
                k = stdscr.getch()
                if k == -1:
                    break
                keys.add(k)

            if not keys:
                time.sleep(0.05)
                continue

            if 27 in keys:  # ESC
                send(arduino, "MOVE stop 0")
                break

            z = ord('z') in keys or ord('Z') in keys or curses.KEY_UP in keys
            s = ord('s') in keys or ord('S') in keys or curses.KEY_DOWN in keys
            q = ord('q') in keys or ord('Q') in keys or curses.KEY_LEFT in keys
            d = ord('d') in keys or ord('D') in keys or curses.KEY_RIGHT in keys
            a = ord('a') in keys or ord('A') in keys
            e = ord('e') in keys or ord('E') in keys
            y = ord('y') in keys or ord('Y') in keys
            u = ord('u') in keys or ord('U') in keys
            i = ord('i') in keys or ord('I') in keys
            o = ord('o') in keys or ord('O') in keys
            space = ord(' ') in keys

            plus  = ord('+') in keys or ord('=') in keys
            minus = ord('-') in keys or ord('_') in keys

            if plus:
                speed = min(255, speed + SPEED_STEP)
                draw()
            if minus:
                speed = max(0, speed - SPEED_STEP)
                draw()

            if space:
                send(arduino, "MOVE stop 0")
            elif y:
                send(arduino, f"MOVE forwardLeft {speed}")
            elif u:
                send(arduino, f"MOVE forwardRight {speed}")
            elif i:
                send(arduino, f"MOVE backwardLeft {speed}")
            elif o:
                send(arduino, f"MOVE backwardRight {speed}")
            elif z:
                send(arduino, f"MOVE forward {speed}")
            elif s:
                send(arduino, f"MOVE backward {speed}")
            elif q:
                send(arduino, f"MOVE left {speed}")
            elif d:
                send(arduino, f"MOVE right {speed}")
            elif a:
                send(arduino, f"MOVE rotateCCW {speed}")
            elif e:
                send(arduino, f"MOVE rotateCW {speed}")
            else:
                send(arduino, "MOVE stop 0")

            time.sleep(0.05)

    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


if __name__ == "__main__":
    arduino = connect_arduino()
    try:
        run(arduino)
    except KeyboardInterrupt:
        pass
    finally:
        send(arduino, "MOVE stop 0")
        arduino.close()
        print("Déconnecté.")
