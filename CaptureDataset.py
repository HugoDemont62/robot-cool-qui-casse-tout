import cv2
import os

# --- Configuration ---
SAVE_FOLDER = "dataset1"
WIDTH = 3264
HEIGHT = 2448
CAMERA_INDEX = 0

# Variable globale pour partager l'état du clic entre la fonction callback et la boucle principale
capture_requested = False

def handle_mouse(event, x, y, flags, param):
    """Fonction qui réagit aux événements de la souris"""
    global capture_requested
    if event == cv2.EVENT_LBUTTONDOWN:  # Déclenche au clic gauche
        capture_requested = True

def main():
    global capture_requested
    
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) # 0 pour désactiver l'autofocus

    # 1. Créer la fenêtre AVANT d'attacher le callback
    window_name = "Previsualisation (Clic ou S pour capturer)"
    cv2.namedWindow(window_name)
    
    # 2. Attacher la fonction de détection de souris à cette fenêtre
    cv2.setMouseCallback(window_name, handle_mouse)

    print("Commandes : Clic GAUCHE ou touche 'S' pour capturer | 'Q' pour quitter")

    img_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = cv2.resize(frame, (1024, 768))
        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(1) & 0xFF

        # On vérifie si 'S' est pressé OU si un clic a été détecté
        if key == ord('s') or capture_requested:
            img_name = os.path.join(SAVE_FOLDER, f"img_{img_counter:03d}.jpg")
            cv2.imwrite(img_name, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            print(f"Capture effectuée ! ({img_name})")
            img_counter += 1
            
            # Réinitialiser le signal de capture
            capture_requested = False

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()