"""
Fichier: main.py
Auteur: Hugo Demont
Version: 1.0.0
"""

import argparse
import sys


def main():
    """
    Fonction principale - Lance l'interface robot.
    
    Analyse les arguments de la ligne de commande et démarre l'interface
    en mode simulation ou en mode normal.
    """
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

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                        🤖 Robot cool qui casse tout 🤖                      ║
║                        Équipe: Pas encore ingénieur                          ║
║                              Eurobot 2026                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        from robot_state import RobotStateManager
        from robot_interface import RobotInterface
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("\nVérifiez que vous êtes dans le bon répertoire et que tous les fichiers existent:")
        print("  - robot_state.py")
        print("  - robot_interface.py")
        sys.exit(1)
    print("📦 Initialisation du gestionnaire d'état...")
    state_manager = RobotStateManager()
    if args.simulation:
        print("🎮 Mode SIMULATION activé - Données fictives générées automatiquement")
        state_manager.start_simulation()
    else:
        print("📡 Mode NORMAL - En attente de données du robot")
        print("   (Utilisez --simulation pour tester sans robot réel)")

    print("🖥️  Création de l'interface graphique...")
    interface = RobotInterface(state_manager)
    
    print("✅ Interface prête! Ouverture de la fenêtre...\n")
    
    # Cette ligne bloque jusqu'à la fermeture de la fenêtre
    interface.run()
    print("\n👋 Fermeture de l'interface...")
    if args.simulation:
        state_manager.stop_simulation()
    print("✅ Au revoir!")

def example_robot_integration():
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
        while running:
            try:
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


if __name__ == "__main__":
    main()
