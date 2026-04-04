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

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "TEST MOTEURS")
            stdscr.addstr(1, 0, "1/2/3/4=test  Espace=stop  ESC=quitter")
            stdscr.refresh()

            k = stdscr.getch()
            if k == 27:  # ESC
                stop()
                break
            elif k == ord(' '):
                stop()
            elif k in moteurs:
                nom, fw, bw, pwm = moteurs[k]
                stdscr.addstr(2, 0, f">> {nom[:38]}")
                stdscr.refresh()
                moteur(fw, bw, pwm, sens=1)
                time.sleep(1.5)
                stop()

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
