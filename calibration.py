from __future__ import print_function
import cv2
import numpy as np
import glob
import os

# --- Paramètres du damier ---
number_of_squares_X = 10 
number_of_squares_Y = 7 

nX = number_of_squares_X - 1 
nY = number_of_squares_Y - 1 
square_size = 0.025  # Taille d'une case en mètres

# Critères d'affinage
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Préparation des points 3D (0,0,0), (1,0,0), (2,0,0) ... (nX-1, nY-1, 0)
object_points_3D = np.zeros((nX * nY, 3), np.float32)
object_points_3D[:, :2] = np.mgrid[0:nX, 0:nY].T.reshape(-1, 2)
object_points_3D *= square_size

object_points = [] 
image_points = [] 

def main():
    # Dossier contenant tes photos 8 Mpx
    images = glob.glob('dataset1/*.jpg')
    
    if not images:
        print("Erreur : Aucune image .jpg trouvée dans 'dataset1/'.")
        return

    pattern = (nX, nY)
    valid_images = 0

    print(f"Analyse de {len(images)} images...")

    for image_file in images:
        img = cv2.imread(image_file)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Détection optimisée pour le grand angle (Adaptive Threshold)
        found, corners = cv2.findChessboardCorners(gray, pattern, 
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK)

        if found:
            object_points.append(object_points_3D)
            
            # Affinage ultra-précis des coins
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            image_points.append(corners2)

            # Visualisation
            cv2.drawChessboardCorners(img, pattern, corners2, found)
            display_resize = cv2.resize(img, (1024, 768)) # Redimension pour écran
            cv2.imshow('Calibration en cours...', display_resize)
            cv2.waitKey(100)
            valid_images += 1
        else:
            print(f"Échec de détection sur : {image_file}")

    cv2.destroyAllWindows()

    if valid_images < 10:
        print(f"Attention : Seulement {valid_images} images valides. Risque d'imprécision.")

    print("\nCalcul de la calibration (Modèle Rational pour 105° FOV)...")
    
    # --- Calibration avec Flags pour Grand Angle ---
    # On utilise CALIB_RATIONAL_MODEL pour gérer la distorsion plus complexe
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        object_points, 
        image_points, 
        gray.shape[::-1], 
        None, 
        None,
        flags=cv2.CALIB_RATIONAL_MODEL + cv2.CALIB_THIN_PRISM_MODEL
    )

    # --- Sauvegarde YAML ---
    output_file = 'calibration_chessboard.yaml'
    cv_file = cv2.FileStorage(output_file, cv2.FILE_STORAGE_WRITE)
    cv_file.write('K', mtx)
    cv_file.write('D', dist)
    cv_file.release()
    print(f"Paramètres sauvegardés dans {output_file}")

    # --- Statistiques ---
    print("\n--- RÉSULTATS ---")
    print("Matrice Intrinsèque (K) :\n", mtx)
    print("\nCoefficients de Distorsion (D) :\n", dist)

    # Calcul de l'erreur de reprojection
    total_error = 0
    for i in range(len(object_points)):
        imgpoints2, _ = cv2.projectPoints(object_points[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(image_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error

    mean_error = total_error / len(object_points)
    print(f"\nErreur moyenne de reprojection : {mean_error:.4f} pixels")
    
    if mean_error < 0.5:
        print("Statut : Calibration EXCELLENTE")
    elif mean_error < 1.0:
        print("Statut : Calibration ACCEPTABLE")
    else:
        print("Statut : Calibration MÉDIOCRE (Vérifiez l'éclairage ou la planéité du damier)")

if __name__ == '__main__':
    main()