#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         MAIN - EUROBOT 2026                                  ║
║                      Équipe: Pas encore ingénieur                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Fichier: main.py
Auteur: Hugo Demont
Version: 1.0.0

DESCRIPTION:
    Point d'entrée principal pour lancer l'interface robot.
    Ce fichier est le seul que vous devez exécuter!

═══════════════════════════════════════════════════════════════════════════════
COMMENT LANCER L'INTERFACE:
═══════════════════════════════════════════════════════════════════════════════

    # Mode normal (attend une vraie connexion robot):
    python main.py

    # Mode simulation (génère des données fictives pour tester):
    python main.py --simulation
    # ou
    python main.py -s

    # Aide:
    python main.py --help

═══════════════════════════════════════════════════════════════════════════════
COMMENT INTÉGRER AVEC VOTRE ROBOT:
═══════════════════════════════════════════════════════════════════════════════

Le code ci-dessous montre comment utiliser le RobotStateManager pour mettre
à jour l'interface avec les données de votre robot réel.

Exemple d'intégration:

    from robot_state import RobotStateManager
    
    # Créer le gestionnaire
    manager = RobotStateManager()
    
    # Dans votre boucle de réception de données (WiFi/Bluetooth):
    def on_data_received(data):
        # Mettre à jour la position
        manager.update_position(
            x=data['x'],
            y=data['y'],
            theta=data['theta']
        )
        
        # Mettre à jour les roues
        for i, wheel_data in enumerate(data['wheels']):
            manager.update_wheel(i, state=wheel_data['state'], speed=wheel_data['speed'])
        
        # Mettre à jour les capteurs
        for i, value in enumerate(data['sensors']):
            manager.update_sensor(i, value)
        
        # etc...

═══════════════════════════════════════════════════════════════════════════════
STRUCTURE DES FICHIERS:
═══════════════════════════════════════════════════════════════════════════════

    robot-cool-qui-casse-tout/
    ├── main.py                 # CE FICHIER - Point d'entrée
    ├── robot_state.py          # Gestion de l'état du robot
    ├── robot_interface.py      # Interface graphique (Tkinter)
    ├── calibration.py          # Calibration caméra (existant)
    ├── pos_estimation.py       # Estimation position ArUco (existant)
    └── requirements.txt        # Dépendances Python

═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import sys


def main():
    """
    Fonction principale - Lance l'interface robot.
    
    Analyse les arguments de la ligne de commande et démarre l'interface
    en mode simulation ou en mode normal.
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # ANALYSE DES ARGUMENTS
    # ─────────────────────────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="🤖 Interface Robot - Eurobot 2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py                 Lance l'interface (mode normal)
  python main.py --simulation    Lance avec données simulées
  python main.py -s              Raccourci pour --simulation

Pour plus d'informations, consultez le README.md
        """
    )
    
    parser.add_argument(
        '-s', '--simulation',
        action='store_true',
        help='Démarre automatiquement le mode simulation avec données fictives'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='Robot Interface v1.0.0 - Eurobot 2026'
    )
    
    args = parser.parse_args()
    
    # ─────────────────────────────────────────────────────────────────────────
    # AFFICHAGE DU BANNER
    # ─────────────────────────────────────────────────────────────────────────
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗  ██████╗ ██████╗  ██████╗ ████████╗    ██╗███╗   ██╗████████╗      ║
║   ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝    ██║████╗  ██║╚══██╔══╝      ║
║   ██████╔╝██║   ██║██████╔╝██║   ██║   ██║       ██║██╔██╗ ██║   ██║         ║
║   ██╔══██╗██║   ██║██╔══██╗██║   ██║   ██║       ██║██║╚██╗██║   ██║         ║
║   ██║  ██║╚██████╔╝██████╔╝╚██████╔╝   ██║       ██║██║ ╚████║   ██║         ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝       ╚═╝╚═╝  ╚═══╝   ╚═╝         ║
║                                                                              ║
║                        🤖 Robot cool qui casse tout 🤖                       ║
║                        Équipe: Pas encore ingénieur                          ║
║                              Eurobot 2026                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # ─────────────────────────────────────────────────────────────────────────
    # IMPORT DES MODULES (fait ici pour afficher le banner rapidement)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        from robot_state import RobotStateManager
        from robot_interface import RobotInterface
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("\nVérifiez que vous êtes dans le bon répertoire et que tous les fichiers existent:")
        print("  - robot_state.py")
        print("  - robot_interface.py")
        sys.exit(1)
    
    # ─────────────────────────────────────────────────────────────────────────
    # CRÉATION ET CONFIGURATION DU GESTIONNAIRE D'ÉTAT
    # ─────────────────────────────────────────────────────────────────────────
    print("📦 Initialisation du gestionnaire d'état...")
    state_manager = RobotStateManager()
    
    # ─────────────────────────────────────────────────────────────────────────
    # MODE SIMULATION (si demandé)
    # ─────────────────────────────────────────────────────────────────────────
    if args.simulation:
        print("🎮 Mode SIMULATION activé - Données fictives générées automatiquement")
        state_manager.start_simulation()
    else:
        print("📡 Mode NORMAL - En attente de données du robot")
        print("   (Utilisez --simulation pour tester sans robot réel)")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CRÉATION ET LANCEMENT DE L'INTERFACE
    # ─────────────────────────────────────────────────────────────────────────
    print("🖥️  Création de l'interface graphique...")
    interface = RobotInterface(state_manager)
    
    print("✅ Interface prête! Ouverture de la fenêtre...\n")
    
    # Cette ligne bloque jusqu'à la fermeture de la fenêtre
    interface.run()
    
    # ─────────────────────────────────────────────────────────────────────────
    # NETTOYAGE À LA FERMETURE
    # ─────────────────────────────────────────────────────────────────────────
    print("\n👋 Fermeture de l'interface...")
    if args.simulation:
        state_manager.stop_simulation()
    print("✅ Au revoir!")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                     EXEMPLE D'INTÉGRATION AVEC LE ROBOT                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def example_robot_integration():
    """
    EXEMPLE: Comment intégrer l'interface avec votre code de communication robot.
    
    Cette fonction n'est pas exécutée automatiquement.
    Copiez et adaptez ce code dans votre propre programme.
    
    ═══════════════════════════════════════════════════════════════════════════
    SCÉNARIO:
    Vous avez un thread qui reçoit des données du robot via WiFi/Bluetooth.
    Vous voulez afficher ces données dans l'interface.
    ═══════════════════════════════════════════════════════════════════════════
    """
    import threading
    import time
    from robot_state import RobotStateManager, WheelState
    from robot_interface import RobotInterface
    
    # Variable pour contrôler l'arrêt propre du thread
    running = True
    
    # 1. Créer le gestionnaire d'état
    manager = RobotStateManager()
    
    # 2. Fonction qui simule la réception de données du robot
    #    (Remplacez par votre vrai code de communication)
    def receive_robot_data():
        """
        Thread de réception des données du robot.
        
        IMPORTANT: La boucle vérifie 'running' pour permettre un arrêt propre.
        """
        while running:
            try:
                # ──────────────────────────────────────────────────────────────
                # ICI: Votre code pour recevoir les données du robot
                # Par exemple via socket WiFi ou Bluetooth
                # ──────────────────────────────────────────────────────────────
                
                # Exemple de données reçues (à remplacer par vos vraies données):
                robot_data = {
                    'x': 1500,        # Position X en mm
                    'y': 1000,        # Position Y en mm
                    'theta': 45,      # Angle en degrés
                    'battery': 85,    # Batterie en %
                    'wheels': [
                        {'state': 'forward', 'speed': 60},
                        {'state': 'forward', 'speed': 60},
                        {'state': 'forward', 'speed': 60},
                        {'state': 'forward', 'speed': 60},
                    ],
                    'sensors': [200, 180, 150, 220, 0, 1, 0],  # Valeurs capteurs
                }
                
                # ──────────────────────────────────────────────────────────────
                # Mettre à jour le gestionnaire d'état
                # ──────────────────────────────────────────────────────────────
                
                # Position
                manager.update_position(
                    x=robot_data['x'],
                    y=robot_data['y'],
                    theta=robot_data['theta']
                )
                
                # Batterie
                manager.set_battery_level(robot_data['battery'])
                
                # Statut connexion
                manager.set_connected(True)
                
                # Roues
                for i, wheel in enumerate(robot_data['wheels']):
                    manager.update_wheel(i, state=wheel['state'], speed=wheel['speed'])
                
                # Capteurs
                for i, value in enumerate(robot_data['sensors']):
                    manager.update_sensor(i, value)
                
            except Exception as e:
                print(f"Erreur de communication: {e}")
                manager.set_connected(False)
            
            # Pause entre les lectures (ajustez selon votre protocole)
            time.sleep(0.1)
    
    # 3. Démarrer le thread de réception en arrière-plan
    recv_thread = threading.Thread(target=receive_robot_data, daemon=True)
    recv_thread.start()
    
    # 4. Créer et lancer l'interface
    interface = RobotInterface(manager)
    interface.run()  # Bloque jusqu'à fermeture
    
    # 5. Arrêt propre du thread (quand la fenêtre est fermée)
    running = False


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          EXÉCUTION DU PROGRAMME                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    main()
