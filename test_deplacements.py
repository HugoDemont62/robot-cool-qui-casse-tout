"""
test_deplacements.py - Teste chaque mouvement un par un et log les résultats

Lance ce script sur le Pi : python test_deplacements.py
Pour chaque mouvement :
  - Le robot bouge 1 seconde
  - Tu notes ce qui se passe (o=correct, i=inversé, a=autre problème, s=skip)
  - Les résultats sont sauvegardés dans resultats_deplacements.txt
"""

import serial
import time
import sys

SERIAL_PORT = '/dev/ttyACM0'
SPEED = 150
DURATION = 1.0  # secondes de mouvement par test

MOUVEMENTS = [
    ("forward",       "Avancer tout droit"),
    ("backward",      "Reculer tout droit"),
    ("right",         "Translation droite (strafe)"),
    ("left",          "Translation gauche (strafe)"),
    ("rotateCW",      "Rotation horaire (sur place)"),
    ("rotateCCW",     "Rotation anti-horaire (sur place)"),
    ("forwardRight",  "Diagonale avant-droite"),
    ("forwardLeft",   "Diagonale avant-gauche"),
    ("backwardRight", "Diagonale arrière-droite"),
    ("backwardLeft",  "Diagonale arrière-gauche"),
]

def send(arduino, cmd):
    arduino.write(f"{cmd}\n".encode())
    arduino.readline()

def move(arduino, direction, speed=SPEED):
    send(arduino, f"MOVE {direction} {speed}")

def stop(arduino):
    send(arduino, "MOVE stop 0")

def main():
    try:
        arduino = serial.Serial(SERIAL_PORT, 9600, timeout=2)
        time.sleep(2)
        print("Connecté à l'Arduino.\n")
    except serial.SerialException as e:
        print(f"Erreur port série : {e}")
        sys.exit(1)

    resultats = []

    print("=" * 55)
    print("TEST DES DÉPLACEMENTS")
    print("=" * 55)
    print("Pour chaque mouvement, note ce qui se passe :")
    print("  o = correct (fait bien ce qui est attendu)")
    print("  i = inversé (part dans le sens opposé)")
    print("  a = autre problème (dévie, tourne, etc.)")
    print("  s = skip (passer)")
    print("  q = quitter")
    print("=" * 55)
    input("\nAppuie sur Entrée pour commencer...")

    for direction, description in MOUVEMENTS:
        print(f"\n>>> TEST : {description.upper()}")
        print(f"    Commande : MOVE {direction} {SPEED}")
        input("    Appuie sur Entrée pour lancer le mouvement...")

        move(arduino, direction)
        time.sleep(DURATION)
        stop(arduino)
        time.sleep(0.3)

        while True:
            rep = input("    Résultat (o/i/a/s/q) + note optionnelle : ").strip().lower()
            if not rep:
                continue
            code = rep[0]
            note = rep[1:].strip() if len(rep) > 1 else ""

            if code == 'q':
                stop(arduino)
                arduino.close()
                _save(resultats)
                print("\nTest interrompu.")
                sys.exit(0)
            elif code in ('o', 'i', 'a', 's'):
                labels = {'o': 'CORRECT', 'i': 'INVERSÉ', 'a': 'AUTRE', 's': 'SKIPPED'}
                resultats.append({
                    "direction": direction,
                    "description": description,
                    "code": code,
                    "label": labels[code],
                    "note": note
                })
                print(f"    -> {labels[code]}" + (f" : {note}" if note else ""))
                break
            else:
                print("    Entrée invalide. Utilise o/i/a/s/q")

    stop(arduino)
    arduino.close()
    _save(resultats)

    print("\n" + "=" * 55)
    print("RÉSUMÉ")
    print("=" * 55)
    for r in resultats:
        note_str = f" ({r['note']})" if r['note'] else ""
        print(f"  {r['direction']:<15} {r['label']}{note_str}")
    print(f"\nRésultats sauvegardés dans resultats_deplacements.txt")

def _save(resultats):
    with open("resultats_deplacements.txt", "w") as f:
        f.write("RÉSULTATS TEST DÉPLACEMENTS\n")
        f.write("=" * 55 + "\n")
        for r in resultats:
            note_str = f" | note: {r['note']}" if r['note'] else ""
            f.write(f"{r['direction']:<15} | {r['label']}{note_str}\n")

if __name__ == "__main__":
    main()
