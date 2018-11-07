# People detector module for fall detection

import cv2
import imutils

class PeopleDetector:

    def detect_human(self, roi):
        pass

class HOGDetector(PeopleDetector):

    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect_human(self, roi):
        roi = imutils.resize(roi, width=max(64, min(100, roi.shape[1])))
        roi = imutils.resize(roi, height=max(128, roi.shape[0]))

        rects, weights = self.hog.detectMultiScale(roi, winStride=(4, 4), padding=(0, 0), scale = 1.05)

        if not len(rects) > 0:
            return False
        else:
            return True
