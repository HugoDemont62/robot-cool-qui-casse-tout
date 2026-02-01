# Documentation du firmware Arduino

Ce document décrit le firmware contenu dans `PEI_-_Code_Arduino.ino` : architecture, mappage des broches, commandes série disponibles, paramètres de calibration, diagnostics et conseils de dépannage.

## Aperçu

Le firmware pilote :
- 4 moteurs DC (mécanum) via ponts H (broches direction + PWM)
- 3 moteurs pas-à-pas DRV8825 (hauteur, pince, translation horizontale)
- 1 moteur 28BYJ-48 via ULN2003 pour la rotation de la caisse
- Un capteur d'origine (fin de course) pour la position horizontale de la pince

La communication avec le PC se fait par le port série (Serial) à 9600 bauds. Le firmware attend des commandes textuelles terminées par `\n` et renvoie `OK` ou `ERR` selon le cas.

---

## Mappage des broches (défini dans le code)

- Moteurs DC (structure Motor):
  - `frontRight`: dir forward=44, dir backward=45, PWM=4
  - `frontLeft`:  dir forward=52, dir backward=53, PWM=2
  - `backRight`:  dir forward=41, dir backward=40, PWM=5
  - `backLeft`:   dir forward=49, dir backward=48, PWM=3

- Steppers DRV8825 (structure StepperMotor):
  - `StepperHorizontal`: steps=22, dir=23
  - `StepperClamp`: steps=24, dir=25
  - `StepperHeight`: steps=26, dir=27

- Stepper 28BYJ-48 via ULN2003 (pour rotation pince): pins = {30, 31, 32, 33}
- Capteur origine pince: `clampOriginSensorPin = 34` (INPUT_PULLUP)

> Remarque : vérifiez le câblage physique avant d'utiliser — les numéros correspondent au script et au schéma utilisé par l'équipe.

---

## Constantes de configuration importantes

- `stepsPerHalfRevolution = 1024` -> pas pour demi-tour du 28BYJ-48
- `stepsPerMilimeterT8 = 512` -> pas/mm pour vis T8 (à calibrer)
- `stepsPerMilimeterHorizontal = 512` -> pas/mm pour translation horizontale (à calibrer)
- `deltaUpDown = 50` mm -> pas par défaut lever/descendre
- `deltaClamp = 5` mm -> pas par défaut ouvrir/fermer la pince

Ajustez ces valeurs selon votre mécanique.

---

## Protocole série (commandes)

Toutes les commandes sont des chaînes ASCII terminées par `\n`. Le firmware lit avec `Serial.readStringUntil('\n')`.
Réponse standard : `OK` (commande acceptée) ou `ERR` / `ERR_*`.

Liste des commandes supportées :

- SET_PIN <pin> <state>
  - Ex : `SET_PIN 13 1` -> met la broche 13 à HIGH
  - Réponse : `OK`

- SET_PWM <pin> <value>
  - Ex : `SET_PWM 4 180` -> envoie PWM 180 sur la broche 4 (0-255)
  - Réponse : `OK`

- MOVE <direction> <speed>
  - Directions : `forward`, `backward`, `right`, `left`, `rotateCW`, `rotateCCW`, `forwardRight`, `forwardLeft`, `backwardRight`, `backwardLeft`, `stop`
  - Speed : entier entre -255 et 255 (sécurité interne via `constrain`)
  - Ex : `MOVE forward 120` ou `MOVE rotateCW 100`
  - Réponse : `OK` ou `ERR_UNKNOWN_MOVE` si direction non reconnue

- ClampRotate
  - Fait tourner la caisse avec le 28BYJ-48 (utilise `stepsPerHalfRevolution`)
  - Ex : `ClampRotate` -> `OK`

- ClampOrigin
  - Réinitialise les compteurs internes `clampPosition`, `clampHeight`, `clampGrip` à 0
  - Ex : `ClampOrigin` -> `OK`

- ClampFindOrigin
  - Déplace horizontalement la pince jusqu'au capteur d'origine (fin de course)
  - Ex : `ClampFindOrigin` -> `OK`

- ClampUp [mm]
  - Monte la pince de `mm` millimètres (si pas de paramètre, utilise `deltaUpDown`)
  - Ex : `ClampUp 20` ou `ClampUp`

- ClampDown [mm]
  - Descend la pince de `mm` millimètres
  - Ex : `ClampDown 20`

- ClampGrab [mm]
  - Ferme la pince (par pas) de `mm` mm (par défaut `deltaClamp`)
  - Ex : `ClampGrab 3`

- ClampRelease [mm]
  - Ouvre la pince de `mm` mm
  - Ex : `ClampRelease 3`

- ClampMoveTo <mm>
  - Déplace la pince à la position horizontale absolute `mm` (en mm)
  - Ex : `ClampMoveTo 120`

---

## Exemples d'utilisation depuis Python (PC)

Exemple minimal en Python utilisant pyserial :

```python
import serial
s = serial.Serial('COM3', 9600, timeout=1)
s.write(b'MOVE forward 120\n')
print(s.readline().decode().strip())  # attend OK
s.write(b'ClampFindOrigin\n')
print(s.readline().decode().strip())
```

Adaptez `COM3` et le timeout.

---

## Variables d'état internes (utile pour diagnostics)

- `clampPosition` : position horizontale actuelle (mm)
- `clampHeight` : hauteur actuelle (mm)
- `clampGrip` : ouverture/fermeture de la pince (mm/pas)

Ces variables sont maintenues côté Arduino et modifiées par les commandes de pince.

---

## Points d'attention / dépannage

- Baudrate : le firmware initialise `Serial.begin(9600);` — assurez-vous que l'application PC utilise le même débit.
- Timeout de lecture : `Serial.readStringUntil('\n')` bloque si la fin de ligne n'est pas envoyée.
- Capteur d'origine : la broche est en `INPUT_PULLUP` — le capteur doit ramener la broche à LOW pour indiquer l'origine.
- PWM pins : vérifiez que les broches définies pour PWM sont compatibles PWM sur votre carte (sur certaines cartes, pas toutes les broches le sont).
