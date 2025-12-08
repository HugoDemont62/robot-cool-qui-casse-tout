"""
File: `pos_estimation.py`
Author: Hugo Demont
Version: 1.0.1
"""
from __future__ import print_function
import argparse
import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R
import math

# mapping existant
ARUCO_DICT = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL
}

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
    return roll_x, pitch_y, yaw_z

def main():
    parser = argparse.ArgumentParser(description="ArUco pose estimation")
    parser.add_argument("--dict", default="DICT_4X4_50", help="ArUco dictionary name (see ARUCO_DICT keys)")
    parser.add_argument("--id", type=int, default=-1, help="Marker ID to follow (-1 = all)")
    parser.add_argument("--size", type=float, default=0.066, help="Marker side length in meters")
    parser.add_argument("--calib", default="calibration_chessboard.yaml", help="Calibration file")
    args = parser.parse_args()

    if args.dict not in ARUCO_DICT:
        print("[INFO] Dictionnaire '{}' non trouvé. Clés disponibles:".format(args.dict))
        for k in ARUCO_DICT.keys():
            print("  -", k)
        return

    # lecture calibration
    cv_file = cv2.FileStorage(args.calib, cv2.FILE_STORAGE_READ)
    if not cv_file.isOpened():
        print("[ERROR] Impossible d'ouvrir", args.calib)
        return
    mtx = cv_file.getNode('K').mat()
    dst = cv_file.getNode('D').mat()
    cv_file.release()

    this_aruco_dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[args.dict])
    this_aruco_parameters = cv2.aruco.DetectorParameters_create()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Impossible d'ouvrir la caméra")
        return

    target_id = args.id

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        corners, marker_ids, _ = cv2.aruco.detectMarkers(frame, this_aruco_dictionary,
                                                         parameters=this_aruco_parameters)

        if marker_ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, marker_ids)
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, args.size, mtx, dst)

            ids_flat = marker_ids.flatten()
            for idx, mid in enumerate(ids_flat):
                mid = int(mid)
                # si on suit un id précis, ignorer les autres
                if target_id != -1 and mid != target_id:
                    continue

                # récupération translation
                tx, ty, tz = map(float, tvecs[idx][0])

                # rotation matrix -> quaternion
                rot_mat = cv2.Rodrigues(rvecs[idx][0])[0]
                r = R.from_matrix(rot_mat)
                quat = r.as_quat()  # x, y, z, w

                rx, ry, rz, rw = quat
                roll_x, pitch_y, yaw_z = euler_from_quaternion(rx, ry, rz, rw)
                roll_x = math.degrees(roll_x)
                pitch_y = math.degrees(pitch_y)
                yaw_z = math.degrees(yaw_z)

                # affichage console (court)
                print(f"ID {mid} -> tx:{tx:.3f} ty:{ty:.3f} tz:{tz:.3f} roll:{roll_x:.1f} pitch:{pitch_y:.1f} yaw:{yaw_z:.1f}")

                # dessiner axes et label cible
                cv2.drawFrameAxes(frame, mtx, dst, rvecs[idx], tvecs[idx], args.size * 0.75)
                # mettre en évidence le marqueur suivi
                corner_pts = corners[idx].reshape((4, 2)).astype(int)
                cv2.polylines(frame, [corner_pts], True, (0, 255, 0), 3)
                cv2.putText(frame, f"ID:{mid}", tuple(corner_pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
