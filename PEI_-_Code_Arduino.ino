#include <Arduino.h>

// --- Config moteurs --- (Av droit / Av gauche / Ar droit / Ar gauche)
const int dirPower[4] = {4, 2, 5, 3}; //PIN PWM pour moteur

struct Motor { int pinForward; int pinBackward; int pinPWM; };

// Définition des moteurs 
Motor frontRight = {44, 45, 4}; 
Motor frontLeft = {52, 53, 2}; 
Motor backRight = {41, 40, 5}; 
Motor backLeft = {49, 48, 3};

// --- Config moteurs DRV8825 (exemple avec 3 moteurs) ---
const int dirPins[3]  = {22, 24, 26};  // DIR pour NEMA
const int stepPins[3] = {23, 25, 27};  // STEP pour NEMA

// --- Config moteur 28BYJ-48 via ULN2003 ---
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


void setup() {
  Serial.begin(9600);

  // Config NEMA
  for (int i=0; i<3; i++) {
    pinMode(dirPins[i], OUTPUT);
    pinMode(stepPins[i], OUTPUT);
  }

  // Config 28BYJ
  for (int i=0; i<4; i++) {
    pinMode(stepperPins[i], OUTPUT);
  }

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
// FONCTIONS DE BASE
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


    // --- NEMA avec DRV8825 ---
    else if (cmd.startsWith("STEP_NEMA")) {
      int motor = cmd.substring(10, cmd.indexOf(' ',10)).toInt();
      int steps = cmd.substring(cmd.indexOf(' ',10)+1).toInt();
      digitalWrite(dirPins[motor], steps > 0 ? HIGH : LOW);
      steps = abs(steps);
      for (int i=0; i<steps; i++) {
        digitalWrite(stepPins[motor], HIGH);
        delayMicroseconds(500);
        digitalWrite(stepPins[motor], LOW);
        delayMicroseconds(500);
      }
      Serial.println("OK");
    }

    // --- 28BYJ-48 ---
    else if (cmd.startsWith("STEP_28BYJ")) {
      int steps = cmd.substring(11).toInt();
      for (int i=0; i<steps; i++) {
        stepIndex = (stepIndex + 1) % 8; // avance
        for (int j=0; j<4; j++) {
          digitalWrite(stepperPins[j], stepSequence[stepIndex][j]);
        }
        delay(1); // ajuste la vitesse
      }
      Serial.println("OK");
    }
  }
} 
