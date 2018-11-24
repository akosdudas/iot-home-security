import numpy as np
import cv2
import imutils
from imutils.object_detection import non_max_suppression
from object_tracker import ImageObject
from scene import Scene
from fgbg import BS, CNT
from utils import undistort_frame

# https://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/
# https://www.theimpossiblecode.com/blog/backgroundsubtractorcnt-opencv-3-3-0/
# https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=12&cad=rja&uact=8&ved=2ahUKEwjErd_QsbTeAhWDiiwKHQWmAXcQFjALegQICBAC&url=http%3A%2F%2Fwww.mdpi.com%2F1424-8220%2F17%2F12%2F2864%2Fpdf&usg=AOvVaw0Z--0buthONx7l6UuDC15-
# Dataset - http://www.iro.umontreal.ca/~labimage/Dataset/


cap = cv2.VideoCapture('/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/chute02/cam8.avi')
#cap = cv2.VideoCapture(0)

bs = CNT()

i = 0

scene = Scene()

while(1):
    ret, frame_orig = cap.read()
    if not ret:
        break
    roi = None
    #frame = undistort_frame(frame_orig)
    frame = frame_orig.copy()
    #frame = cv2.GaussianBlur(frame,(5,5),1)
    #noise_free = cv2.medianBlur(frame, 3)

    #frame = imutils.resize(frame, width=min(500, frame.shape[1]))

    fgmask = bs.get_mask(frame)

    if True:    
        mask = bs.denoise_mask()
    else:
        mask = fgmask.copy()

    _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rects = []
    #rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    #rects = non_max_suppression(rects, probs=None, overlapThresh=0.65)

    objects = []

    for contour in contours:
        obj = ImageObject(0, contour, frame)
        if obj.get_area() < 1000:
            continue
        if obj.get_area() > 50000:
            continue
        if obj.detect_human():
            #print(f"HUMAN {i}")
            i += 1
        objects.append(obj)
        #scene.add_object(obj)
    scene.update_objects(objects)

    for i, o in scene.objects.items():
        o.draw(frame)


    cv2.imshow('f',mask)
    cv2.imshow('fr', frame)
    k = cv2.waitKey() & 0xff
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()