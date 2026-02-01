#include <Arduino.h>

// --- Config moteurs --- (Av droit / Av gauche / Ar droit / Ar gauche)
const int dirPower[4] = {4, 2, 5, 3}; //PIN PWM pour moteur

struct Motor { int pinForward; int pinBackward; int pinPWM; };

// Définition des moteurs 
Motor frontRight = {44, 45, 4}; 
Motor frontLeft = {52, 53, 2}; 
Motor backRight = {41, 40, 5}; 
Motor backLeft = {49, 48, 3};

// --- Config moteurs DRV8825 ---
struct StepperMotor { int steps; int dir; int enable };
StepperMotor StepperHorizontal = {22, 23, 6}; // Moteur horizontal
StepperMotor StepperClamp = {24, 25, 7}; // Moteur de pince
StepperMotor StepperHeight = {26, 27, 8}; // Moteur de hauteur

// --- Config moteur 28BYJ-48 via ULN2003 ---
// Utiliser dans la commande ClampRotate
const int stepperPins[4] = {30, 31, 32, 33};
int stepIndex = 0;
const int stepSequence[8][4] = {
  {1,0,0,0},
  {1,1,0,0},
  {0,1,0,0},
  {0,1,1,0},
  {0,0,1,0},
  {0,0,1,1},
  {0,0,0,1},
  {1,0,0,1}
};

// --- Capteur origine horizontal --- 
const int clampOriginSensorPin = 34; // À ajuster selon câblage

// --- Config mouvement de base ---
const int stepsPerHalfRevolution = 1024; // Nombre de pas par demi rotation du 28BYJ-48 (FULL STEP)
const int stepsPerMilimeterT8 = 512; // Nombre de pas par mm pour les vis T8 (à ajuster selon le mécanisme)
const int stepsPerMilimeterHorizontal= 512; // Nombre de pas pour avancer de 1 mm (à ajuster selon le mécanisme)
const int deltaUpDown = 50; // Décalage en mm pour lever/abaisser la caisse
const int deltaClamp = 5; // Décalage en mm pour ouvrir/fermer la pince

// --- Etats Internes ---
long clampPosition = 0; // Position actuelle de la pince (en mm)
long clampHeight = 0; // Position actuelle horizontale (en mm)
long clampGrip = 0; // Position actuelle de la pince (ouverte/fermée) (en pas)

void setup() {
  Serial.begin(9600);

  // Config NEMA
  pinMode(StepperHorizontal.dir, OUTPUT);
  pinMode(StepperClamp.dir, OUTPUT);
  pinMode(StepperHeight.dir, OUTPUT);
  pinMode(StepperHorizontal.steps, OUTPUT);
  pinMode(StepperClamp.steps, OUTPUT);
  pinMode(StepperHeight.steps, OUTPUT);

  pinMode(StepperHorizontal.enable, OUTPUT);
  pinMode(StepperClamp.enable, OUTPUT);
  pinMode(StepperHeight.enable, OUTPUT);

  digitalWrite(StepperHorizontal.enable, HIGH);
  digitalWrite(StepperClamp.enable, HIGH);
  digitalWrite(StepperHeight.enable, HIGH);

  // Config 28BYJ
  for (int i=0; i<4; i++) {
    pinMode(stepperPins[i], OUTPUT);
  }

  // Capteur origine 
  pinMode(clampOriginSensorPin, INPUT_PULLUP);

  //config moteur
  pinMode(frontRight.pinForward, OUTPUT); 
  pinMode(frontRight.pinBackward, OUTPUT); 
  pinMode(frontLeft.pinForward, OUTPUT); 
  pinMode(frontLeft.pinBackward, OUTPUT); 
  pinMode(backRight.pinForward, OUTPUT); 
  pinMode(backRight.pinBackward, OUTPUT); 
  pinMode(backLeft.pinForward, OUTPUT); 
  pinMode(backLeft.pinBackward, OUTPUT); 
  
  pinMode(frontRight.pinPWM, OUTPUT); 
  pinMode(frontLeft.pinPWM, OUTPUT); 
  pinMode(backRight.pinPWM, OUTPUT); 
  pinMode(backLeft.pinPWM, OUTPUT);
}


// ===============================
// FONCTIONS DE BASE MOTEURS
// ===============================

// Commande un moteur avec une vitesse (-255 à +255)
void setMotor(Motor m, int speed) {
  if (speed > 0) {
    digitalWrite(m.pinForward, HIGH);
    digitalWrite(m.pinBackward, LOW);
    analogWrite(m.pinPWM, speed);
  } 
  else if (speed < 0) {
    digitalWrite(m.pinForward, LOW);
    digitalWrite(m.pinBackward, HIGH);
    analogWrite(m.pinPWM, -speed);
  } 
  else {
    digitalWrite(m.pinForward, LOW);
    digitalWrite(m.pinBackward, LOW);
    analogWrite(m.pinPWM, 0);
  }
}

// Coupe tous les moteurs
void stopAll() {
  setMotor(frontRight, 0);
  setMotor(frontLeft, 0);
  setMotor(backRight, 0);
  setMotor(backLeft, 0);
}


// ===============================
// MOUVEMENTS MÉCANUM
// ===============================

// Avancer
void forward(int speed) {
  setMotor(frontRight, speed);
  setMotor(frontLeft, speed);
  setMotor(backRight, speed);
  setMotor(backLeft, speed);
}

// Reculer
void backward(int speed) {
  forward(-speed);
}

// Translation droite
void right(int speed) {
  setMotor(frontRight,  speed);
  setMotor(frontLeft,  -speed);
  setMotor(backRight, -speed);
  setMotor(backLeft,   speed);
}

// Translation gauche
void left(int speed) {
  right(-speed);
}

// Rotation horaire
void rotateCW(int speed) {
  setMotor(frontRight,  speed);
  setMotor(frontLeft,  -speed);
  setMotor(backRight,   speed);
  setMotor(backLeft,   -speed);
}

// Rotation anti-horaire
void rotateCCW(int speed) {
  rotateCW(-speed);
}

// Diagonale avant droite
void forwardRight(int speed) {
  setMotor(frontRight, 0);
  setMotor(frontLeft, speed);
  setMotor(backRight, speed);
  setMotor(backLeft, 0);
}

// Diagonale avant gauche
void forwardLeft(int speed) {
  setMotor(frontRight, speed);
  setMotor(frontLeft, 0);
  setMotor(backRight, 0);
  setMotor(backLeft, speed);
}

// Diagonale arrière droite
void backwardRight(int speed) {
  setMotor(frontRight, -speed);
  setMotor(frontLeft, 0);
  setMotor(backRight, 0);
  setMotor(backLeft, -speed);
}

// Diagonale arrière gauche
void backwardLeft(int speed) {
  setMotor(frontRight, 0);
  setMotor(frontLeft, -speed);
  setMotor(backRight, -speed);
  setMotor(backLeft, 0);
}

// ===============================
// FONCTIONS STEPPER DRV8825
// ===============================
void moveSteppers(StepperMotor motor, long steps, bool direction) {
  digitalWrite(motor.dir, direction ? HIGH : LOW);
  for (long i = 0; i < steps; i++) {
    digitalWrite(motor.steps, HIGH);
    delayMicroseconds(1000); // Ajuster la vitesse ici
    digitalWrite(motor.steps, LOW);
    delayMicroseconds(1000); // Ajuster la vitesse ici
  }
}

// ===============================
// FONCTIONS PREHENSION
// ===============================

//Rotation de la caisse
void clampRotate() {
  for (int i=0; i<abs(stepsPerHalfRevolution); i++) {
    stepIndex = (stepIndex + (stepsPerHalfRevolution > 0 ? 1 : 7)) % 8; // avance ou recule
    for (int j=0; j<4; j++) {
      digitalWrite(stepperPins[j], stepSequence[stepIndex][j]);
    }
    delay(1); // ajuste la vitesse
  }
}

void ClampOrigin() {
  clampHeight = 0;
  clampGrip = 0;
  clampPosition = 0;
}

void ClampFindOrigin() {
  digitalWrite(StepperHorizontal.dir, LOW); // retour arrière

  while (digitalRead(clampOriginSensorPin) == HIGH) {
    digitalWrite(StepperHorizontal.steps, HIGH);
    delayMicroseconds(500);
    digitalWrite(StepperHorizontal.steps, LOW);
    delayMicroseconds(500);
  }
  clampPosition = 0;
}

void ClampUp(int mm = deltaUpDown) {
  moveStepper(StepperHeight, mm * stepsPerMilimeterT8, true);
  clampHeight += mm;
}

void ClampDown(int mm = deltaUpDown) {
  moveStepper(StepperHeight, mm * stepsPerMilimeterT8, false);
  clampHeight -= mm;
}

void ClampGrab(int mm = deltaClamp) {
  moveStepper(StepperClamp, mm * stepsPerMilimeterT8, true);
  clampGrip += mm;
}

void ClampRelease(int mm = deltaClamp) {
  moveStepper(StepperClamp, mm * stepsPerMilimeterT8, false);
  clampGrip -= mm;
}

void ClampMoveTo(int mm) {
  long delta = mm - clampPosition;
  bool direction = delta > 0;
  moveStepper(StepperHorizontal, abs(delta) * stepsPerMilimeterHorizontal, direction);
  clampPosition = mm;
}

// ===============================
// CODE PRINCIPAL
// ===============================

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    // --- Ports numériques ---
    if (cmd.startsWith("SET_PIN")) {
      int pin = cmd.substring(8, cmd.indexOf(' ',8)).toInt();
      int state = cmd.substring(cmd.indexOf(' ',8)+1).toInt();
      pinMode(pin, OUTPUT);
      digitalWrite(pin, state);
      Serial.println("OK");
    }

    // --- Ports analogiques (PWM) ---
    else if (cmd.startsWith("SET_PWM")) {
      int pin = cmd.substring(8, cmd.indexOf(' ',8)).toInt();
      int value = cmd.substring(cmd.indexOf(' ',8)+1).toInt();
      pinMode(pin, OUTPUT);
      analogWrite(pin, value); // 0-255
      Serial.println("OK");
    }

    // --- Deplacement ---
    else if (cmd.startsWith("MOVE")) {
      // Extraction direction et vitesse
      int firstSpace = cmd.indexOf(' ');
      int secondSpace = cmd.indexOf(' ', firstSpace + 1);
    
      if (firstSpace < 0 || secondSpace < 0) {
        Serial.println("ERR");
        return;
      }
    
      String movingDirection = cmd.substring(firstSpace + 1, secondSpace);
      int movingSpeed = cmd.substring(secondSpace + 1).toInt();
    
      // Sécurité vitesse
      movingSpeed = constrain(movingSpeed, -255, 255);
    
      // === MAPPING DES COMMANDES MÉCANUM ===
      if (movingDirection == "forward") forward(movingSpeed);
      else if (movingDirection == "backward") backward(movingSpeed);
      else if (movingDirection == "right") right(movingSpeed);
      else if (movingDirection == "left") left(movingSpeed);
      else if (movingDirection == "rotateCW") rotateCW(movingSpeed);
      else if (movingDirection == "rotateCCW") rotateCCW(movingSpeed);
      else if (movingDirection == "forwardRight") forwardRight(movingSpeed);
      else if (movingDirection == "forwardLeft") forwardLeft(movingSpeed);
      else if (movingDirection == "backwardRight") backwardRight(movingSpeed);
      else if (movingDirection == "backwardLeft") backwardLeft(movingSpeed);
      else if (movingDirection == "stop") stopAll();
    
      else {
        Serial.println("ERR_UNKNOWN_MOVE");
        return;
      }
      Serial.println("OK");
    }
    
    // --- CommandePince ---
    else if (cmd.startsWith("ClampRotate")) {
      clampRotate();
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampOrigin")) {
      ClampOrigin();
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampFindOrigin")) {
      ClampFindOrigin();
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampUp")) {
      int mm = cmd.length() > 8 ? cmd.substring(8).toInt() : deltaUpDown;
      ClampUp(mm);
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampDown")) {
      int mm = cmd.length() > 10 ? cmd.substring(10).toInt() : deltaUpDown;
      ClampDown(mm);
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampGrab")) {
      int mm = cmd.length() > 10 ? cmd.substring(10).toInt() : deltaClamp;
      ClampGrab(mm);
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampRelease")) {
      int mm = cmd.length() > 13 ? cmd.substring(13).toInt() : deltaClamp;
      ClampRelease(mm);
      Serial.println("OK");
    }

    else if (cmd.startsWith("ClampMoveTo")) {
      int mm = cmd.substring(12).toInt();
      ClampMoveTo(mm);
      Serial.println("OK");
    }
  }
}