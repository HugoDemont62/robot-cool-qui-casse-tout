import serial
import time
import curses

arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

def send_command(cmd):
    arduino.write((cmd + "\n").encode())
    response = arduino.readline().decode().strip()
    print(f"> {cmd} -> {response}")
    return response

def keyboard_control():
    SPEED = 200

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)  # lecture non bloquante

    stdscr.addstr(0, 0, "Pilotage robot (SSH OK)")
    stdscr.addstr(1, 0, "Z=Avancer | S=Reculer | Q=Gauche | D=Droite")
    stdscr.addstr(2, 0, "A=Rot Gauche | E=Rot Droite")
    stdscr.addstr(3, 0, "Y/U/I/O = Diagonales | Suppr=Quitter")
    stdscr.addstr(5, 0, "Maintiens les touches pour bouger...")

    try:
        while True:
            keys = set()

            # Lire toutes les touches pressées pendant ce cycle
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                keys.add(key)

            # Quitter avec SUPPR
            if curses.KEY_DC in keys:
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

            # --- PRIORITÉ : diagonales sur Y U I O ---
            if y:
                # choisis la diagonale que tu veux; exemple: avant gauche
                send_command(f"MOVE forwardLeft {SPEED}")
            elif u:
                # exemple: avant droite
                send_command(f"MOVE forwardRight {SPEED}")
            elif i:
                # exemple: arrière gauche
                send_command(f"MOVE backwardLeft {SPEED}")
            elif o:
                # exemple: arrière droite
                send_command(f"MOVE backwardRight {SPEED}")

            # --- MOUVEMENTS SIMPLES ---
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

            # --- AUCUNE TOUCHE : STOP ---
            else:
                send_command("MOVE stop 0")

            time.sleep(0.05)

    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


if __name__ == "__main__":
    keyboard_control()
