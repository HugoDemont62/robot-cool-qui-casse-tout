# 🎮 Guide de Contrôle Direct du Robot

## 📋 Nouveautés v2.0

Cette version ajoute un contrôle **direct** du robot depuis l'interface Python, sans passer par SSH vers le Raspberry Pi.

### ✨ Nouvelles fonctionnalités

1. **Connexion série directe** à l'Arduino via USB
2. **Panneau de contrôle** avec boutons pour tous les mouvements
3. **Contrôle de la pince** depuis l'interface
4. **Log en temps réel** des commandes envoyées
5. **Détection automatique** des ports série disponibles

---

## 🚀 Installation

### 1. Installer la nouvelle dépendance

```bash
pip install pyserial
```

Ou installer toutes les dépendances :

```bash
pip install -r requirements.txt
```

### 2. Connecter l'Arduino

- Branchez l'Arduino en USB sur votre ordinateur
- Notez le port série (ex: `/dev/ttyACM0` sur Linux, `COM3` sur Windows)

### 3. Lancer l'interface

```bash
python main.py
```

---

## 🎮 Utilisation

### Étape 1: Connexion au robot

1. Ouvrez l'onglet **"🎮 Contrôle Direct"**
2. Cliquez sur **🔄** pour rafraîchir la liste des ports
3. Sélectionnez le port de votre Arduino
4. Cliquez sur **🔌 Connecter**
5. Le statut devient **✅ Connecté** en vert

### Étape 2: Contrôler le robot

#### 🚗 Déplacement

Utilisez la grille de contrôle directionnel :

```
↖    ⬆ Avancer    ↗
⬅ Gauche  STOP  Droite ➡
↙    ⬇ Reculer    ↘
```

- **Boutons diagonaux** : déplacements diagonaux
- **⟲ / ⟳** : rotation sur place
- **Slider de vitesse** : ajuster de 0 à 255
- **⏹ STOP** : arrêt d'urgence

#### 🦾 Pince

Contrôles disponibles :

- **⬆ Monter** : élève la pince
- **⬇ Descendre** : abaisse la pince
- **✊ Saisir** : ferme la pince
- **✋ Relâcher** : ouvre la pince
- **🔄 Rotation** : fait pivoter la pince
- **🏠 Origine** : retour à la position de référence

### Étape 3: Surveiller les commandes

Le **log des commandes** en bas affiche :
- Les commandes envoyées (→)
- Les réponses de l'Arduino
- Les erreurs éventuelles

---

## 🔧 Architecture

```
┌─────────────────┐
│   Interface     │
│   Python        │
│   (Tkinter)     │
└────────┬────────┘
         │ USB Série
         │ (pyserial)
         │
┌────────▼────────┐
│    Arduino      │
│  (PEI_Code)     │
└────────┬────────┘
         │
┌────────▼────────┐
│   Moteurs +     │
│   Pince         │
└─────────────────┘
```

**Avantages :**
- ✅ Pas besoin de SSH
- ✅ Pas besoin du Raspberry Pi
- ✅ Contrôle direct depuis le PC
- ✅ Feedback instantané
- ✅ Idéal pour les tests

---

## 🐛 Dépannage

### "Module pyserial non disponible"

**Solution :**
```bash
pip install pyserial
```

### "Aucun port série trouvé"

**Causes possibles :**
1. Arduino non branché en USB
2. Drivers USB non installés
3. Port utilisé par un autre programme

**Solutions :**
- Vérifiez le branchement USB
- Installez les drivers CH340/FTDI si nécessaire
- Fermez Arduino IDE ou autres programmes série

### "Impossible de se connecter au port"

**Solutions :**
- Vérifiez les permissions (Linux) : `sudo chmod 666 /dev/ttyACM0`
- Ajoutez-vous au groupe dialout : `sudo usermod -a -G dialout $USER`
- Redémarrez votre session

### L'Arduino ne répond pas

**Vérifications :**
1. Le bon sketch est téléversé (`PEI_-_Code_Arduino.ino`)
2. Le baudrate est bien 9600 (dans le code Arduino ET Python)
3. Le câble USB fonctionne (pas seulement alimentation)

---

## 📝 Commandes disponibles

### Mouvement
- `MOVE forward <vitesse>` - Avancer
- `MOVE backward <vitesse>` - Reculer
- `MOVE left <vitesse>` - Gauche
- `MOVE right <vitesse>` - Droite
- `MOVE rotateCW <vitesse>` - Rotation horaire
- `MOVE rotateCCW <vitesse>` - Rotation anti-horaire
- `MOVE forwardLeft <vitesse>` - Diagonale avant-gauche
- `MOVE forwardRight <vitesse>` - Diagonale avant-droite
- `MOVE backwardLeft <vitesse>` - Diagonale arrière-gauche
- `MOVE backwardRight <vitesse>` - Diagonale arrière-droite
- `MOVE stop 0` - Arrêt

### Pince
- `ClampUp [mm]` - Monter
- `ClampDown [mm]` - Descendre
- `ClampGrab [mm]` - Fermer
- `ClampRelease [mm]` - Ouvrir
- `ClampRotate` - Rotation 180°
- `ClampFindOrigin` - Chercher l'origine
- `ClampMoveTo <mm>` - Position spécifique

### Général
- `SET_PIN <pin> <0|1>` - Contrôle pin digital
- `SET_PWM <pin> <0-255>` - Contrôle PWM

---

## 💡 Astuces

### Test rapide
1. Connectez-vous au robot
2. Testez avec **⏹ STOP** pour vérifier la connexion
3. Utilisez une vitesse faible (50-100) pour les premiers tests
4. Gardez toujours le bouton d'arrêt d'urgence accessible

### Mode hybride
Vous pouvez utiliser :
- **Contrôle Direct** pour les tests et débogage
- **Simulation** pour développer sans matériel
- Les deux en même temps (simulation + contrôle)

### Raccourcis clavier
Pour ajouter des raccourcis clavier, vous pouvez modifier le code :
```python
self.root.bind('<Up>', lambda e: self._send_move("forward"))
self.root.bind('<Down>', lambda e: self._send_move("backward"))
self.root.bind('<Left>', lambda e: self._send_move("left"))
self.root.bind('<Right>', lambda e: self._send_move("right"))
self.root.bind('<space>', lambda e: self._stop_robot())
```

---

## 📞 Support

En cas de problème :
1. Vérifiez le log des commandes
2. Testez la communication série avec `robot_serial.py` directement
3. Vérifiez les connexions matérielles
4. Consultez les fichiers README existants

---

## 🎯 Prochaines étapes

**Fonctionnalités à développer :**
- [ ] Enregistrement de séquences de mouvements
- [ ] Mode "joystick" avec touches clavier
- [ ] Graphiques temps réel des capteurs
- [ ] Sauvegarde/chargement de configurations
- [ ] Mode "pilote automatique" avec waypoints

**Bon courage pour Eurobot 2026 ! 🏆**

---

*Équipe : Pas encore ingénieur*  
*Robot : Robot cool qui casse tout*
