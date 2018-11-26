import numpy as np 
import cv2

import imutils
from imutils.object_detection import non_max_suppression

from enum import Enum

from .people_detector import HOGDetector, MobileNetSSD

from .state_predictor import State, StatePredictor

#from utils import plotter

class ObjectType(Enum):
    OBJECT = 0
    HUMAN = 1

class ImageObject:

    # Padding to be added to all sides of the ROI for the object
    PADDING = 30
    MATCH_AREA_TRESHOLD = 2


    def __init__(self, obj_id, contour, frame):
        self.id = obj_id        
        self.contour = contour
        self.type = ObjectType.OBJECT
        self.roi = self.get_roi(frame)

        self.unseen = 0
        self.people_detector = HOGDetector()
        self.sp = StatePredictor(initial_pred_state=self.get_state())

        self.state_history = [self.get_state()]
        self.predict_state_history = [self.predict_state()]

    def update_state(self, matching_obj):
        self.contour = matching_obj.contour
        self.roi = matching_obj.roi
        self.unseen = 0
        if not self.type == ObjectType.HUMAN:
            self.type = matching_obj.type

        self.state_history.append(self.get_state())
        self.predict_state_history.append(self.predict_state())

    def predict_state(self):
        return self.sp.predict_state(self.get_state())

    def get_state(self):
        cm = self.get_center_of_mass()
        if cm == None:
            rect = self.get_rect_wh()
            cm = (rect[0] + rect[2]/2, rect[1] + rect[3]/2)
        x, y, w, h = self.get_rect_wh()
        angle = self.get_angle()
        if not angle:
            angle = 0
        return State(cm[0], cm[1], h, w, angle)

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

    def get_rect_area(self):
        x,y,w,h = self.get_rect_wh()
        return w*h

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
        (x,y,u,v) = self.get_rect()
        cv2.putText(frame, obj_text, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.5 ,color,1,cv2.LINE_AA)
        ellipse = self.get_ellipse()
        if ellipse:
            cv2.ellipse(frame, ellipse, (0,255,0), 2)

        self.state_history[-1].draw(frame)
        self.predict_state_history[-1].draw(frame)

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

    def find_match_candidates(self, detected_objects: list):
        candidates = []
        predicted_state = self.predict_state_history[-1]
        for obj in detected_objects:
            area_ratio = float(predicted_state.get_area()) / obj.state_history[-1].get_area()
            if area_ratio < ImageObject.MATCH_AREA_TRESHOLD and area_ratio > 1.0/ImageObject.MATCH_AREA_TRESHOLD:
                candidates.append({"mc_obj": obj, "dist_sq": predicted_state.dist_square_from(obj.state_history[-1])})
        return candidates
        #return sorted(candidates, key=lambda k: k['dist_sq'])
        
    @staticmethod
    def merge_objects(objects: list, frame):
        # convexhull, approxpoly
        
        if not objects:
            raise AttributeError('Cannot merge an empty list of ImageObjects')

        # Merge object contours
        merged_contours = np.concatenate([o.contour for o in objects])
        hull = cv2.convexHull(merged_contours, returnPoints=True)
        merged_object = ImageObject(0, hull, frame)
        return merged_object
        

if __name__ == '__main__':
    image_orig = cv2.imread('/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/rand_images/German-Sheperd-Image-1-composite.jpg', cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(image, 127, 255, 0)
    im2, contours, hierarchy = cv2.findContours(cv2.bitwise_not(thresh), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)    
    objects = []
    for c in contours:
        objects.append(ImageObject(0, c, image_orig))
    merged = ImageObject.merge_objects(objects, image_orig)
    cv2.polylines(image_orig, [merged.contour], isClosed=True, color=(0,0,255), thickness=3)
    cv2.imshow('test_image', image_orig)
    cv2.waitKey()
    cv2.destroyAllWindows()