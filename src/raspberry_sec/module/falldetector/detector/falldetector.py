import numpy as np
import cv2
import imutils

from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject
from raspberry_sec.module.falldetector.detector.scene import Scene
from raspberry_sec.module.falldetector.detector.fgbg import BS, CNT
from raspberry_sec.module.falldetector.detector.utils import undistort_frame

class FallDetector():

    def __init__(self):
        self.bs = CNT()
        self.scene = Scene()
        self.human_cnt = 0
        self.frame = None
        self.mask = None

    def process_frame(self, input_frame, timestamp):
        # Resize frame to uniform size
        self.frame = imutils.resize(input_frame, width=min(500, input_frame.shape[1]))
        # Background subtraction
        fgmask = self.bs.get_mask(self.frame)
        # Remove noise from the foreground mask
        self.mask = self.bs.denoise_mask()
        # Find object contours on the foreground mask
        _, contours, _ = cv2.findContours(self.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Gather detected objects from the foreground mask
        objects = []

        for contour in contours:
            obj = ImageObject(0, contour, self.frame, timestamp)
            if obj.get_area() < 1000:
                continue
            if obj.get_area() > 50000:
                continue
            if obj.detect_human():
                self.human_cnt += 1
            objects.append(obj)
        self.scene.update_objects(objects, self.frame, timestamp)

        # TODO detect fall, respond with True if a human fall was detected, False otherwise
        return False

    def draw(self):
        # If there were no processed frames, drawing is not possible
        if self.frame is None:
            return
        for i, o in self.scene.objects.items():
            o.draw(self.frame)

if __name__ == '__main__':
    cap = cv2.VideoCapture('/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/chute01/cam8.avi')
    fd = FallDetector()

    while(1):
        ret, frame = cap.read()
        if not ret:
            break

        fd.process_frame(frame)
        fd.draw()

        cv2.imshow('frame', fd.frame)

        k = cv2.waitKey(1) & 0xff
        if k == 27:
            break
        # If b key is pressed, execute pass statement for possible breakpoint
        elif k == 66 or k == 98:
            pass
    
    cap.release()
    cv2.destroyAllWindows()
