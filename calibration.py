"""
File: `calibration.py`
Author: Hugo Demont
Version: 1.0.1 (correction pattern size + reprojection error)
"""
from __future__ import print_function
import cv2
import numpy as np
import glob

number_of_squares_X = 10
number_of_squares_Y = 7
nX = number_of_squares_X - 1  # inner corners per row
nY = number_of_squares_Y - 1  # inner corners per column
square_size = 0.025  # m

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

object_points_3D = np.zeros((nX * nY, 3), np.float32)
object_points_3D[:, :2] = np.mgrid[0:nX, 0:nY].T.reshape(-1, 2)
object_points_3D *= square_size

object_points = []
image_points = []


def main():
    # change the glob if your images are in a subfolder, e.g. 'images/*.jpg'
    images = glob.glob('*.jpg')
    if not images:
        print("Aucune image trouvée dans le dossier courant.")
        return

    pattern = (nX, nY)
    for image_file in images:
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, pattern, None)
        if found:
            object_points.append(object_points_3D)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            image_points.append(corners2)
            cv2.drawChessboardCorners(image, pattern, corners2, found)
            cv2.imshow("Chessboard", image)
            cv2.waitKey(500)

    if not object_points:
        print("Aucun coin détecté. Vérifiez les images et le pattern.")
        return

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(object_points,
                                                       image_points,
                                                       gray.shape[::-1],
                                                       None,
                                                       None)

    # save
    cv_file = cv2.FileStorage('calibration_chessboard.yaml', cv2.FILE_STORAGE_WRITE)
    cv_file.write('K', mtx)
    cv_file.write('D', dist)
    cv_file.release()

    # load (example)
    cv_file = cv2.FileStorage('calibration_chessboard.yaml', cv2.FILE_STORAGE_READ)
    mtx_loaded = cv_file.getNode('K').mat()
    dist_loaded = cv_file.getNode('D').mat()
    cv_file.release()

    print("Camera matrix:")
    print(mtx_loaded)
    print("\nDistortion coefficients:")
    print(dist_loaded)

    # reprojection error
    total_error = 0
    for i in range(len(object_points)):
        imgpoints2, _ = cv2.projectPoints(object_points[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(image_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error
    print("\nMean reprojection error:", total_error / len(object_points))

    cv2.destroyAllWindows()


if __name__ == '__main__':
    print(__doc__)
    main()
