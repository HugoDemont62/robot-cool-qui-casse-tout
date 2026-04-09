"""
test_moteurs.py - Identifie chaque moteur un par un

Lance ce script sur le Pi : python test_moteurs.py

Appuie sur 1, 2, 3, 4 pour tester chaque moteur séparément.
Note quelle roue bouge et dans quel sens pour chaque touche.
"""

import serial
import time
import sys
import curses

SERIAL_PORT = '/dev/ttyACM0'
SPEED = 150

def run(arduino):
    import curses
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)

    def stop():
        arduino.write(b"MOVE stop 0\n")
        arduino.readline()

    def moteur(fw_pin, bw_pin, pwm_pin, sens=1):
        stop()
        time.sleep(0.1)
        if sens > 0:
            arduino.write(f"SET_PIN {bw_pin} 0\nSET_PIN {pwm_pin} 1\nSET_PIN {fw_pin} 1\n".encode())
        else:
            arduino.write(f"SET_PIN {fw_pin} 0\nSET_PIN {pwm_pin} 1\nSET_PIN {bw_pin} 1\n".encode())

    moteurs = {
        ord('1'): ("Moteur A  (code: frontRight) pins 52/48/50", 52, 48, 50),
        ord('2'): ("Moteur B  (code: frontLeft)  pins 49/53/51", 49, 53, 51),
        ord('3'): ("Moteur C  (code: backRight)  pins 46/42/44", 46, 42, 44),
        ord('4'): ("Moteur D  (code: backLeft)   pins 43/47/45", 43, 47, 45),
    }

    def clamp_cmd(cmd):
        arduino.write(f"{cmd}\n".encode())
        arduino.readline()

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "TEST MOTEURS & PINCE")
            stdscr.addstr(1, 0, "--- Roues ---")
            stdscr.addstr(2, 0, "1/2/3/4=test roue  Espace=stop")
            stdscr.addstr(3, 0, "--- Pince ---")
            stdscr.addstr(4, 0, "u=monter   d=descendre  g=saisir  r=relacher")
            stdscr.addstr(5, 0, "o=origine  f=find origin  t=rotation")
            stdscr.addstr(6, 0, "ESC=quitter")
            stdscr.refresh()

            k = stdscr.getch()
            if k == 27:  # ESC
                stop()
                break
            elif k == ord(' '):
                stop()
            elif k in moteurs:
                nom, fw, bw, pwm = moteurs[k]
                stdscr.addstr(7, 0, f">> {nom[:38]}")
                stdscr.refresh()
                moteur(fw, bw, pwm, sens=1)
                time.sleep(1.5)
                stop()
            elif k == ord('u'):
                stdscr.addstr(7, 0, ">> Pince : monter")
                stdscr.refresh()
                clamp_cmd("ClampUp")
            elif k == ord('d'):
                stdscr.addstr(7, 0, ">> Pince : descendre")
                stdscr.refresh()
                clamp_cmd("ClampDown")
            elif k == ord('g'):
                stdscr.addstr(7, 0, ">> Pince : saisir")
                stdscr.refresh()
                clamp_cmd("ClampGrab")
            elif k == ord('r'):
                stdscr.addstr(7, 0, ">> Pince : relacher")
                stdscr.refresh()
                clamp_cmd("ClampRelease")
            elif k == ord('o'):
                stdscr.addstr(7, 0, ">> Pince : reset origine")
                stdscr.refresh()
                clamp_cmd("ClampOrigin")
            elif k == ord('f'):
                stdscr.addstr(7, 0, ">> Pince : recherche origine...")
                stdscr.refresh()
                clamp_cmd("ClampFindOrigin")
            elif k == ord('t'):
                stdscr.addstr(7, 0, ">> Pince : rotation")
                stdscr.refresh()
                clamp_cmd("ClampRotate")

            time.sleep(0.05)

    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

if __name__ == "__main__":
    try:
        arduino = serial.Serial(SERIAL_PORT, 9600, timeout=1)
        time.sleep(2)
        print("Connecté. Lancement du test...")
        run(arduino)
    except serial.SerialException as e:
        print(f"Erreur port série : {e}")
    finally:
        try:
            arduino.write(b"MOVE stop 0\n")
            arduino.close()
        except:
            pass
