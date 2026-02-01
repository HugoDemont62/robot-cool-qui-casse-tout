import argparse
import logging
from typing import Optional, Tuple, Dict, Any

import cv2
import numpy as np

# ------------------------------
# PARAMÈTRES GLOBAUX
# ------------------------------

# Type de dictionnaire ArUco utilisé (4x4, 50 tags possibles)
ARUCO_DICT = cv2.aruco.DICT_4X4_50

# Tailles des différents types de tags (en millimètres)
TAG_SIZES_MM = {
    "ref": 100,     # Tags de référence (grands)
    "small": 40,    # Petits tags
    "default": 70   # Taille standard
}

# Conversion des tailles en mètres (utilisé par OpenCV)
TAG_SIZES_M = {k: v / 1000.0 for k, v in TAG_SIZES_MM.items()}

# Liste des tags servant à définir le repère global
REFERENCE_TAGS = {20, 21, 22, 23}

# Liste des petits tags
SMALL_TAGS = {36, 41, 47}

# Position des tags de référence dans le repère Eurobot (en mètres)
REFERENCE_GLOBAL_POS = {
    20: np.array([600.0, 1400.0, 0.0]) / 1000.0,
    21: np.array([2400.0, 1400.0, 0.0]) / 1000.0,
    22: np.array([600.0, 600.0, 0.0]) / 1000.0,
    23: np.array([2400.0, 600.0, 0.0]) / 1000.0
}

# ------------------------------
# TRANSFORMATIONS
# ------------------------------

def invert_transform(rvec, tvec):
    """
    Inverse une transformation (rotation + translation).
    Permet de passer de "caméra → tag" à "tag → caméra".
    """
    R, _ = cv2.Rodrigues(rvec)
    R_inv = R.T               # Inversion d'une rotation = transposée
    t_inv = -R_inv @ tvec     # Inversion de la translation
    rvec_inv, _ = cv2.Rodrigues(R_inv)
    return rvec_inv, t_inv


def compose_transform(rvec1, tvec1, rvec2, tvec2):
    """
    Compose deux transformations successives :
    (R1, t1) suivie de (R2, t2).
    Permet de chaîner les repères.
    """
    R1, _ = cv2.Rodrigues(rvec1)
    R2, _ = cv2.Rodrigues(rvec2)
    R = R1 @ R2               # Composition des rotations
    t = R1 @ tvec2 + tvec1    # Composition des translations
    rvec, _ = cv2.Rodrigues(R)
    return rvec, t


def compute_detection_weight(corners):
    """
    Calcule un poids basé sur la qualité de détection du tag.
    Plus les coins sont réguliers, plus le poids est élevé.
    Sert à fusionner plusieurs mesures.
    """
    pts = np.asarray(corners).reshape(-1, 2)
    center = pts.mean(axis=0)
    error = np.mean(np.linalg.norm(pts - center, axis=1))
    return 1.0 / (error + 1e-6)


def orthonormalize_rotation(R: np.ndarray) -> np.ndarray:
    """
    Corrige une matrice de rotation approchée pour la rendre orthogonale.
    Utilise une SVD pour obtenir la rotation la plus proche.
    """
    U, S, Vt = np.linalg.svd(R)
    R_proj = U @ Vt
    if np.linalg.det(R_proj) < 0:
        U[:, -1] *= -1
        R_proj = U @ Vt
    return R_proj


# ------------------------------
# PROGRAMME PRINCIPAL
# ------------------------------

def main() -> None:
    """
    Boucle principale :
    - détecte les tags ArUco
    - calcule la pose de la caméra dans le repère Eurobot
    - affiche la position globale des autres tags
    """

    # Lecture des arguments (calibration, caméra, mode verbose)
    parser = argparse.ArgumentParser()
    parser.add_argument('--calib', default='calibration_chessboard.yaml', help='Fichier de calibration')
    parser.add_argument('--cam', type=int, default=0, help='Index de la caméra')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    # Configuration du logger
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='[%(levelname)s] %(message)s')
    log = logging.getLogger('pos_estimation')

    # Chargement des paramètres de calibration caméra
    cv_file = cv2.FileStorage(args.calib, cv2.FILE_STORAGE_READ)
    if not cv_file.isOpened():
        log.error('Impossible d ouvrir %s', args.calib)
        return

    mtx = cv_file.getNode('K').mat()   # Matrice intrinsèque
    dst = cv_file.getNode('D').mat()   # Coefficients de distorsion
    cv_file.release()

    # Initialisation du détecteur ArUco
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    # Ouverture de la caméra
    cap = cv2.VideoCapture(args.cam)
    if not cap.isOpened():
        log.error('Impossible d ouvrir la caméra %d', args.cam)
        return

    log.info("Système prêt. Appuyez sur 'q' pour quitter.")

    # Variables pour stocker la pose globale de la caméra
    global_cam_rvec = None
    global_cam_tvec = None
    global_fixed = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Détection des tags dans l'image
            corners, ids, rejected = detector.detectMarkers(frame)

            ref_poses = []   # Poses des tags de référence
            other_tags = {}  # Poses des autres tags

            if ids is not None:
                ids = ids.flatten()

                for i, tag_id in enumerate(ids):

                    # Sélection de la taille du tag selon son type
                    if tag_id in REFERENCE_TAGS:
                        marker_length = TAG_SIZES_M["ref"]
                    elif tag_id in SMALL_TAGS:
                        marker_length = TAG_SIZES_M["small"]
                    else:
                        marker_length = TAG_SIZES_M["default"]

                    # Estimation de la pose du tag détecté
                    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                        corners[i], marker_length, mtx, dst
                    )
                    rvec = rvecs[0, 0]
                    tvec = tvecs[0, 0]

                    # Affichage des axes du tag
                    cv2.drawFrameAxes(frame, mtx, dst, rvec, tvec, marker_length * 0.75)

                    # Si c'est un tag de référence → utilisé pour fixer le repère global
                    if tag_id in REFERENCE_TAGS:
                        weight = compute_detection_weight(corners[i])
                        ref_poses.append((tag_id, rvec, tvec, weight))

                        cv2.polylines(frame, [corners[i].astype(int)], True, (0, 255, 0), 3)
                        cv2.putText(frame, f"REF {tag_id}",
                                    tuple(corners[i][0][0].astype(int)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Sinon → tag normal
                    else:
                        other_tags[tag_id] = (rvec, tvec, corners[i])

                        cv2.polylines(frame, [corners[i].astype(int)], True, (255, 0, 0), 2)
                        cv2.putText(frame, f"ID {tag_id}",
                                    tuple(corners[i][0][0].astype(int)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # ------------------------------
            # CALCUL DE LA POSE GLOBALE DE LA CAMÉRA
            # ------------------------------

            if not global_fixed and len(ref_poses) >= 1:

                # Fusion pondérée des poses caméra→tag
                R_sum = np.zeros((3, 3))
                t_sum = np.zeros(3)
                w_sum = 0.0

                for tag_id, rvec, tvec, w in ref_poses:
                    R, _ = cv2.Rodrigues(rvec)
                    R_sum += w * R
                    t_sum += w * tvec
                    w_sum += w

                if w_sum > 1e-8:
                    R_avg = R_sum / w_sum
                    t_avg = t_sum / w_sum

                    # Correction de la rotation
                    R_proj = orthonormalize_rotation(R_avg)
                    rvec_fused, _ = cv2.Rodrigues(R_proj)
                    tvec_fused = t_avg

                    # Inversion pour obtenir caméra → tag20
                    rvec_cam_to_tag20, tvec_cam_to_tag20 = invert_transform(rvec_fused, tvec_fused)

                    # Position connue du tag 20 dans le repère Eurobot
                    tag20_global = REFERENCE_GLOBAL_POS[20]
                    rvec_tag20_global = np.array([0.0, 0.0, 0.0])  # Hypothèse : axes alignés
                    tvec_tag20_global = tag20_global

                    # Composition pour obtenir caméra → repère global
                    global_cam_rvec, global_cam_tvec = compose_transform(
                        rvec_tag20_global, tvec_tag20_global,
                        rvec_cam_to_tag20, tvec_cam_to_tag20
                    )

                    global_fixed = True
                    log.info('Repère global Eurobot fixé.')

            # ------------------------------
            # CALCUL DES POSITIONS GLOBALES DES AUTRES TAGS
            # ------------------------------

            if global_fixed:

                for tag_id, (rvec_tag, tvec_tag, c) in other_tags.items():

                    # Transformation repère global → tag
                    rvec_rel, tvec_rel = compose_transform(
                        global_cam_rvec, global_cam_tvec,
                        rvec_tag, tvec_tag
                    )

                    # Conversion en millimètres pour affichage
                    x, y, z = tvec_rel * 1000.0

                    log.info('[TAG %d] Position globale Eurobot : X=%.1f mm Y=%.1f mm Z=%.1f mm',
                             tag_id, x, y, z)

                    # Affichage de la position sur l'image
                    corner0 = np.asarray(c[0][0]).astype(int)
                    cv2.putText(frame, f"({x:.0f},{y:.0f},{z:.0f})",
                                (corner0[0], corner0[1] + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            # ------------------------------
            # AFFICHAGE
            # ------------------------------

            cv2.imshow("Aruco Global Pose (Eurobot)", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()