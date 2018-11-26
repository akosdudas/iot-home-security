# People detector module for fall detection

import cv2
import imutils
import numpy as np

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
            return (False, )
        else:
            return (True, )

class MobileNetSSD(PeopleDetector):

    CLASSES = ( 'background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 
                'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 
                'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor')

    COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

    PROTOTXT = '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/mobilenet_ssd/MobileNetSSD_deploy.prototxt'
    CAFFE_MODEL = '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/mobilenet_ssd/MobileNetSSD_deploy.caffemodel'

    CONFIDENCE_LIMIT = 0.5

    def __init__(self, prototxt = None, caffe_model = None):
        prototxt = MobileNetSSD.PROTOTXT
        caffe_model = MobileNetSSD.CAFFE_MODEL
        self.net = cv2.dnn.readNetFromCaffe(prototxt, caffe_model)
        self.detections = None

    def preprocess_image(self, image):
        return cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)

    def detect_human(self, roi):
        roi_proc = self.preprocess_image(roi)
        self.net.setInput(roi_proc)
        detections = self.net.forward()

        self.detections = {}

        for i in np.arange(0, detections.shape[2]):
            detection = {}
            confidence = detections[0,0,i,2]
            if confidence > MobileNetSSD.CONFIDENCE_LIMIT:
                class_label = int(detections[0,0,i,1])
                self.detections[class_label] = confidence
        
        if 15 in self.detections.keys():
            return (True, self.detections)
        else:
            return (False, self.detections)
        


if __name__ == '__main__':
    cap = cv2.VideoCapture('/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/chute02/cam8.avi')
    net = MobileNetSSD()
    while True:
        ret, frame_orig = cap.read()
        if not ret:
            break
        net.detect_human(frame_orig)
        cv2.imshow('fr', frame_orig)
        k = cv2.waitKey(1) & 0xff
        if k == 27:
            break
    pass
