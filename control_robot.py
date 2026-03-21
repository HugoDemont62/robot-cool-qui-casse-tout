import serial
import time

# Configuration
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)


def send_command(cmd):
    """Envoie une commande à l'Arduino"""
    arduino.write((cmd + "\n").encode())
    response = arduino.readline().decode().strip()
    print(f"> {cmd} -> {response}")
    return response


def keyboard_control_interactive():
    """Mode interactif avec curses (nécessite un terminal)"""
    import curses

    SPEED = 200

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)

    stdscr.addstr(0, 0, "🤖 Pilotage robot (SSH OK)")
    stdscr.addstr(1, 0, "Z=Avancer | S=Reculer | Q=Gauche | D=Droite")
    stdscr.addstr(2, 0, "A=Rot Gauche | E=Rot Droite")
    stdscr.addstr(3, 0, "Y/U/I/O = Diagonales | ESC=Quitter")
    stdscr.addstr(5, 0, "Maintiens les touches pour bouger...")

    try:
        while True:
            keys = set()

            # Lire toutes les touches pressées
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                keys.add(key)

            # ESC ou Suppr pour quitter
            if 27 in keys or curses.KEY_DC in keys:  # ESC = 27
                send_command("MOVE stop 0")
                break

            # Flags touches
            z = ord('z') in keys or ord('Z') in keys
            q = ord('q') in keys or ord('Q') in keys
            s = ord('s') in keys or ord('S') in keys
            d = ord('d') in keys or ord('D') in keys
            a = ord('a') in keys or ord('A') in keys
            e = ord('e') in keys or ord('E') in keys
            y = ord('y') in keys or ord('Y') in keys
            u = ord('u') in keys or ord('U') in keys
            i = ord('i') in keys or ord('I') in keys
            o = ord('o') in keys or ord('O') in keys

            # Diagonales (priorité)
            if y:
                send_command(f"MOVE forwardLeft {SPEED}")
            elif u:
                send_command(f"MOVE forwardRight {SPEED}")
            elif i:
                send_command(f"MOVE backwardLeft {SPEED}")
            elif o:
                send_command(f"MOVE backwardRight {SPEED}")
            # Mouvements simples
            elif z:
                send_command(f"MOVE forward {SPEED}")
            elif s:
                send_command(f"MOVE backward {SPEED}")
            elif q:
                send_command(f"MOVE left {SPEED}")
            elif d:
                send_command(f"MOVE right {SPEED}")
            elif a:
                send_command(f"MOVE rotateCCW {SPEED}")
            elif e:
                send_command(f"MOVE rotateCW {SPEED}")
            else:
                send_command("MOVE stop 0")

            time.sleep(0.05)

    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


def stdin_control():
    """Mode sans TTY : lit les commandes depuis stdin (une par ligne).
    Utilisé quand lancé via SSH sans terminal (interface graphique)."""
    import sys

    SPEED = 200
    cmd_map = {
        'z': f'MOVE forward {SPEED}',
        's': f'MOVE backward {SPEED}',
        'q': f'MOVE left {SPEED}',
        'd': f'MOVE right {SPEED}',
        'a': f'MOVE rotateCCW {SPEED}',
        'e': f'MOVE rotateCW {SPEED}',
        'y': f'MOVE forwardLeft {SPEED}',
        'u': f'MOVE forwardRight {SPEED}',
        'i': f'MOVE backwardLeft {SPEED}',
        'o': f'MOVE backwardRight {SPEED}',
        'stop': 'MOVE stop 0',
    }

    print("stdin_control ready", flush=True)
    try:
        for line in sys.stdin:
            key = line.strip().lower()
            if not key:
                continue
            if key == 'quit':
                send_command("MOVE stop 0")
                break
            if key in cmd_map:
                send_command(cmd_map[key])
            else:
                print(f"Commande inconnue: {key}", flush=True)
    except (KeyboardInterrupt, EOFError):
        send_command("MOVE stop 0")


if __name__ == "__main__":
    import sys
    if sys.stdin.isatty():
        keyboard_control_interactive()
    else:
        stdin_control()
