# Utility functions for fall detection

import cv2
import numpy as np

CAMERA_MATRIX_8 = np.matrix('470.561316433381705 0 355.172484892247837; 0 425.594571513702249 231.057027802762576; 0 0 1')
DIST_8 = np.matrix('-0.412750560124808 0.148158881927254 -0.002749158333180 -0.000425978486412 0.000000000000000')


def undistort_frame(frame):
    fh, fw = frame.shape[:2]
    newcameramtx, roi=cv2.getOptimalNewCameraMatrix(CAMERA_MATRIX_8,DIST_8,(fw,fh),1,(fw,fh))
    frame_undist = cv2.undistort(frame, CAMERA_MATRIX_8, DIST_8, None, newcameramtx)
    x,y,w,h = roi
    return frame_undist[y:y+h, x:x+w]