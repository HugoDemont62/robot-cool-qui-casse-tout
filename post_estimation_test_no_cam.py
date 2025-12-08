import argparse
import cv2
import numpy as np
import math
from scipy.spatial.transform import Rotation as R

ARUCO_DICT = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
}

def make_marker_image_from_dict(aruco_dict, marker_id, marker_px):
    # Essayer drawMarker si disponible
    try:
        tmp = np.zeros((marker_px, marker_px), dtype=np.uint8)
        cv2.aruco.drawMarker(aruco_dict, int(marker_id), marker_px, tmp, 1)
        return tmp
    except Exception:
        pass

    # Fallback : reconstruire depuis bytesList
    if not hasattr(aruco_dict, "bytesList"):
        raise RuntimeError(
            "Impossible de créer le marqueur : ni `drawMarker` ni `bytesList` disponibles.\n"
            "Installe `opencv-contrib-python` si possible :\n"
            "`pip install -U opencv-contrib-python`"
        )

    bl = aruco_dict.bytesList[int(marker_id)]
    arr = np.array(bl, copy=True)

    # Si la structure est 1D (valeurs 0/1 linéaires) : essayer d'inférer la taille
    if arr.ndim == 1:
        if hasattr(aruco_dict, "markerSize") and aruco_dict.markerSize > 0:
            msize = int(aruco_dict.markerSize)
        else:
            # tentative : racine carrée
            msize = int(np.sqrt(arr.size))
            if msize * msize != arr.size:
                # fallback à 7x7 pour éviter erreur brutale
                msize = max(4, int(np.sqrt(arr.size)))
        try:
            marker = arr.reshape((msize, msize))
        except Exception:
            marker = arr.copy()
    elif arr.ndim >= 2:
        # prendre les deux dernières dimensions
        marker = arr.reshape(arr.shape[-2], arr.shape[-1])
    else:
        raise RuntimeError("Format inattendu pour `bytesList`.")

    marker = marker.astype(np.uint8)
    # valeurs attendues 0/1 -> convertir en 0/255
    if marker.max() <= 1:
        marker = marker * 255

    # Redimensionner à marker_px (preserve blocks) avec nearest neighbor
    if (marker.shape[0], marker.shape[1]) != (marker_px, marker_px):
        marker = cv2.resize(marker, (marker_px, marker_px), interpolation=cv2.INTER_NEAREST)

    return marker

def create_transformed_marker(aruco_dict, marker_id, marker_px=200, angle_deg=0, scale=1.0):
    marker = make_marker_image_from_dict(aruco_dict, marker_id, marker_px)
    marker_bgr = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
    h, w = marker_bgr.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle_deg, scale)
    transformed = cv2.warpAffine(marker_bgr, M, (w, h), borderValue=(255,255,255))
    mask = cv2.cvtColor(transformed, cv2.COLOR_BGR2GRAY) < 128
    return transformed, mask

def paste_marker(frame, marker_img, mask, top_left):
    x, y = top_left
    h, w = marker_img.shape[:2]
    fh, fw = frame.shape[:2]
    # si partiellement hors frame, recadrer pour coller la partie visible
    if x >= fw or y >= fh or x + w <= 0 or y + h <= 0:
        return frame
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(fw, x + w)
    y1 = min(fh, y + h)
    mx0 = x0 - x
    my0 = y0 - y
    mx1 = mx0 + (x1 - x0)
    my1 = my0 + (y1 - y0)
    roi = frame[y0:y1, x0:x1]
    m = mask[my0:my1, mx0:mx1]
    mi = marker_img[my0:my1, mx0:mx1]
    roi[m] = mi[m]
    frame[y0:y1, x0:x1] = roi
    return frame

def euler_from_quaternion(x, y, z, w):
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)
    return math.degrees(roll_x), math.degrees(pitch_y), math.degrees(yaw_z)

def main():
    parser = argparse.ArgumentParser(description="Test ArUco without camera")
    parser.add_argument("--dict", default="DICT_4X4_50", help="ArUco dictionary name")
    parser.add_argument("--id", type=int, default=23, help="Marker ID to generate/detect")
    parser.add_argument("--size", type=float, default=0.066, help="Marker side in meters (for pose)")
    parser.add_argument("--show", action="store_true", help="Afficher la fenêtre")
    parser.add_argument("--marker_px", type=int, default=220, help="Taille du marqueur en pixels")
    args = parser.parse_args()

    if args.dict not in ARUCO_DICT:
        print("Dictionnaire inconnu. Clés:", list(ARUCO_DICT.keys()))
        return

    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[args.dict])
    try:
        detector_params = cv2.aruco.DetectorParameters_create()
    except AttributeError:
        detector_params = cv2.aruco.DetectorParameters()

    W, H = 1280, 720
    frame = np.full((H, W, 3), 255, dtype=np.uint8)

    positions = [(100, 100), (400, 50), (800, 200), (200, 400)]
    angles = [0, 25, -15, 45]
    scales = [1.0, 0.9, 1.1, 0.8]

    for pos, ang, sc in zip(positions, angles, scales):
        marker_img, mask = create_transformed_marker(aruco_dict, args.id, marker_px=args.marker_px, angle_deg=ang, scale=sc)
        frame = paste_marker(frame, marker_img, mask, pos)

    fx = fy = 800.0
    cx, cy = W / 2.0, H / 2.0
    mtx = np.array([[fx, 0, cx],
                    [0, fy, cy],
                    [0,  0,  1]], dtype=np.float64)
    dist = np.zeros((5, 1), dtype=np.float64)

    corners, ids, rejected = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=detector_params)
    if ids is None:
        print("Aucun marqueur détecté.")
    else:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, args.size, mtx, dist)
        for i, mid in enumerate(ids.flatten()):
            tx, ty, tz = map(float, tvecs[i][0])
            rot_mat = cv2.Rodrigues(rvecs[i][0])[0]
            r = R.from_matrix(rot_mat)
            qx, qy, qz, qw = r.as_quat()
            roll, pitch, yaw = euler_from_quaternion(qx, qy, qz, qw)
            print(f"ID {int(mid)} -> tx:{tx:.3f} ty:{ty:.3f} tz:{tz:.3f} roll:{roll:.1f} pitch:{pitch:.1f} yaw:{yaw:.1f}")
            try:
                cv2.drawFrameAxes(frame, mtx, dist, rvecs[i], tvecs[i], args.size * 0.75)
            except Exception:
                pass

    if args.show:
        cv2.imshow('synthetic', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        out = 'pos_estimation_test_result.png'
        cv2.imwrite(out, frame)
        print(f"Image sauvegardée: {out}")

if __name__ == "__main__":
    main()
