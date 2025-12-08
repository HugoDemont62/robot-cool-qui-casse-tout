"""
File: `calibration.py`
Author: Hugo Demont
Version: 1.0.0
"""
from __future__ import print_function
import cv2
import numpy as np
import glob

number_of_squares_X = 10
number_of_squares_Y = 7
nX = number_of_squares_X - 1
nY = number_of_squares_Y - 1
square_size = 0.025

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

object_points_3D = np.zeros((nX * nY, 3), np.float32)
object_points_3D[:, :2] = np.mgrid[0:nY, 0:nX].T.reshape(-1, 2)
object_points_3D = object_points_3D * square_size

object_points = []
image_points = []


def main():
    images = glob.glob('*.jpg')
    for image_file in images:
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        success, corners = cv2.findChessboardCorners(gray, (nY, nX), None)
        if success == True:
            object_points.append(object_points_3D)
            corners_2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            image_points.append(corners_2)
            cv2.drawChessboardCorners(image, (nY, nX), corners_2, success)
            cv2.imshow("Image", image)
            cv2.waitKey(1000)

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(object_points,
                                                       image_points,
                                                       gray.shape[::-1],
                                                       None,
                                                       None)

    cv_file = cv2.FileStorage('calibration_chessboard.yaml', cv2.FILE_STORAGE_WRITE)
    cv_file.write('K', mtx)
    cv_file.write('D', dist)
    cv_file.release()

    cv_file = cv2.FileStorage('calibration_chessboard.yaml', cv2.FILE_STORAGE_READ)
    mtx = cv_file.getNode('K').mat()
    dst = cv_file.getNode('D').mat()
    cv_file.release()

    print("Camera matrix:")
    print(mtx)
    print("\n Distortion coefficient:")
    print(dist)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    print(__doc__)
    main()
