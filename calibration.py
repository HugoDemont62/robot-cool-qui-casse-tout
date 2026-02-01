from __future__ import print_function
import cv2
import numpy as np
import glob

# --- Paramètres du damier utilisé pour la calibration ---
number_of_squares_X = 10    # Nombre de cases horizontal du damier
number_of_squares_Y = 7     # Nombre de cases vertical du damier

# Le nombre de coins internes est égal au nombre de cases - 1
nX = number_of_squares_X - 1    # Nombre de coins internes par ligne
nY = number_of_squares_Y - 1    # Nombre de coins internes par colonne

square_size = 0.025  # Taille d’une case du damier (en mètres).

# Critère d’arrêt pour l’algorithme d’affinement des coins (cornerSubPix)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,        # Nombre max d’itérations
            0.001)     # Précision minimale

# --- Préparation des points 3D du damier dans le repère réel ---
# On crée une grille régulière représentant les coins internes du damier
object_points_3D = np.zeros((nX * nY, 3), np.float32)
object_points_3D[:, :2] = np.mgrid[0:nX, 0:nY].T.reshape(-1, 2)

# Mise à l’échelle selon la taille réelle des cases
object_points_3D *= square_size

# Listes qui contiendront les points 3D (réels) et 2D (images)
object_points = []   # Points du damier dans le monde réel
image_points = []    # Points détectés sur les images

def main():
    # Recherche de toutes les images .jpg dans le dossier courant
    # Modifier le chemin si les images sont dans un sous-dossier (ex : 'images/*.jpg')
    images = glob.glob('dataset1/*.jpg')
    if not images:
        print("Aucune image trouvée dans le dossier.")
        return

    pattern = (nX, nY)  # Dimensions du motif de coins à détecter

    # --- Parcours de toutes les images---
    for image_file in images:
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Conversion en niveaux de gris

        # Détection des coins internes du damier
        found, corners = cv2.findChessboardCorners(gray, pattern, None)

        if found:
            # Ajout des points 3D correspondant au damier
            object_points.append(object_points_3D)

            # Affinement de la position des coins détectés
            corners2 = cv2.cornerSubPix(gray, corners,
                                        (11, 11),   # Taille de la fenêtre de recherche
                                        (-1, -1),   # Pas de zone morte
                                        criteria)

            # Ajout des points 2D détectés
            image_points.append(corners2)

            # Affichage des coins détectés sur l’image
            cv2.drawChessboardCorners(image, pattern, corners2, found)
            cv2.imshow("Chessboard", image)
            cv2.waitKey(500)  # Pause pour visualiser chaque image

    if not object_points:
        print("Aucun coin détecté. Vérifiez les images et le pattern.")
        return

    # --- Calibration de la caméra ---
    # Cette fonction calcule :
    # - la matrice intrinsèque (mtx)
    # - les coefficients de distorsion (dist)
    # - les vecteurs de rotation (rvecs)
    # - les vecteurs de translation (tvecs)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        object_points,
        image_points,
        gray.shape[::-1],  # Taille des images
        None,
        None
    )

    # --- Sauvegarde des paramètres de calibration ---
    cv_file = cv2.FileStorage('calibration_chessboard.yaml', cv2.FILE_STORAGE_WRITE)
    cv_file.write('K', mtx)   # Matrice intrinsèque
    cv_file.write('D', dist)  # Coefficients de distorsion
    cv_file.release()

    # --- Exemple de rechargement des paramètres ---
    cv_file = cv2.FileStorage('calibration_chessboard.yaml', cv2.FILE_STORAGE_READ)
    mtx_loaded = cv_file.getNode('K').mat()
    dist_loaded = cv_file.getNode('D').mat()
    cv_file.release()

    print("Matrice de la caméra (intrinsics) :")
    print(mtx_loaded)
    print("\nCoefficients de distorsion :")
    print(dist_loaded)

    # --- Calcul de l’erreur de reprojection ---
    # Permet d’évaluer la qualité de la calibration
    total_error = 0
    for i in range(len(object_points)):
        imgpoints2, _ = cv2.projectPoints(object_points[i],
                                          rvecs[i],
                                          tvecs[i],
                                          mtx,
                                          dist)
        # Erreur entre les points projetés et les points réellement détectés
        error = cv2.norm(image_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error

    print("\nErreur moyenne de reprojection :", total_error / len(object_points))

    cv2.destroyAllWindows()

if __name__ == '__main__':
    print(__doc__)
    main()