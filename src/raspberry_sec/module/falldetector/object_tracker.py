import numpy as np 
import cv2

import imutils
from imutils.object_detection import non_max_suppression

from enum import Enum

from people_detector import HOGDetector, MobileNetSSD

class ObjectType(Enum):
    OBJECT = 0
    HUMAN = 1

class ImageObject:

    # Padding to be added to all sides of the ROI for the object
    PADDING = 30

    def __init__(self, obj_id, contour, frame):
        self.id = obj_id
        self.contour = contour
        self.type = ObjectType.OBJECT
        self.roi = self.get_roi(frame)

        self.unseen = 0

        self.people_detector = MobileNetSSD()

    def get_roi(self, frame):
        x,y,u,v = self.get_rect()
        xR = max(0, x - ImageObject.PADDING)
        yR = max(0, y - ImageObject.PADDING)
        uR = min(frame.shape[1] - 1, u + ImageObject.PADDING)
        vR = min(frame.shape[0] - 1, v + ImageObject.PADDING)
        return frame[yR:vR, xR:uR]
        try:
            roi = cv2.cvtColor(frame[yR:vR, xR:uR], cv2.COLOR_BGR2GRAY).copy()
        except:
            roi = None

        return roi

    def get_area(self):
        return cv2.contourArea(self.contour)

    def get_center_of_mass(self):
        ellipse = self.get_ellipse()
        if not ellipse:
            return None
        
        return ellipse[0]

    def get_rect_wh(self):
        return cv2.boundingRect(self.contour)

    def get_rect(self):
        x,y,w,h = self.get_rect_wh()
        return (x, y, x + w, y + h)


    def get_ellipse(self):
        try:
            return cv2.fitEllipse(self.contour)
        except:
            # Ellipse can only be fit to contours with 5 or more points 
            return None

    def get_angle(self):
        ellipse = self.get_ellipse()
        if ellipse:
            # The 3rd parameter of the ellipse is the angle of the ellipse
            return (90 - ellipse[2])/180*np.pi
        else:
            # If an ellipse could not be fit, return none instead of the angle
            return None

    def get_line_repr(self):
        ellipse = self.get_ellipse()
        if not ellipse:
            return None
        angle = self.get_angle()
        cx, cy = ellipse[0]
        b, a = ellipse[1]

        p1 = (int(cx - a/2 * np.cos(angle)), int(cy + a/2 * np.sin(angle)))
        p2 = (int(cx + a/2 * np.cos(angle)), int(cy - a/2 * np.sin(angle)))

        return (p1, p2)

    def detect_human(self):
        roi = self.roi.copy()

        if self.people_detector.detect_human(roi)[0]:
            self.type = ObjectType.HUMAN
            return True
        else:
            self.TYPE = ObjectType.OBJECT
            return False
    
    def get_pose(self):
        x,y,w,h = self.get_rect_wh()
        ratio = h / w
        if ratio > 1.5:
            pose = "STANDING"
        elif ratio > 0.5:
            pose = "SITTING"
        else:
            pose = "LYING"
        return pose

    def draw(self, frame):
        if self.type == ObjectType.HUMAN:
            obj_text = f"{self.id} HUMAN - {self.get_pose()}"
            color = (0,0,255)
        else:
            obj_text = f"{self.id} OBJECT"
            color = (255,0,0)
        x,y,u,v = self.get_rect()
        cv2.rectangle(frame, (x, y), (u, v), color, 2)
        cv2.putText(frame, obj_text, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.5 ,color,1,cv2.LINE_AA)
        ellipse = self.get_ellipse()
        if ellipse:
            cv2.ellipse(frame, ellipse, (0,255,0), 2)
            pA, pB = self.get_line_repr()
            cv2.line(frame, pA, pB, (0,255,0), 1)

    def distance_square_from(self, other):
        cm_self = self.get_center_of_mass()
        cm_other = other.get_center_of_mass()

        x = cm_self[0] - cm_other[0]
        y = cm_self[1] - cm_other[1]

        return x*x + y*y

    def contains(self, other):
        cm_other = other.get_center_of_mass()
        x,y,u,v = self.get_rect()
        return x < cm_other[0] < u and y < cm_other[1] < v 


        