import numpy as np 
import cv2
import imutils

from enum import Enum
from types import SimpleNamespace

from raspberry_sec.module.falldetector.detector.state_predictor import State, StatePredictor

#from utils import plotter

class ObjectType(Enum):
    OBJECT = 0
    HUMAN = 1

class ImageObject:

    # Padding to be added to all sides of the ROI for the object
    PADDING = 30
    MATCH_AREA_TRESHOLD = 2
    STATE_HISTORY_MAX_LEN = 500
    STANDING_THRESHOLD = 1.5
    LYING_THRESHOLD = 0.5
    LYING_THRESHOLD_ANGLE = np.pi / 4

    @staticmethod
    def configure(padding, match_area_threshold, state_history_max_len,
                  standing_threshold, lying_threshold, lying_threshold_angle):
        ImageObject.PADDING = padding
        ImageObject.MATCH_AREA_TRESHOLD = match_area_threshold
        ImageObject.STATE_HISTORY_MAX_LEN = state_history_max_len
        ImageObject.STANDING_THRESHOLD = standing_threshold
        ImageObject.LYING_THRESHOLD = lying_threshold
        ImageObject.LYING_THRESHOLD_ANGLE = lying_threshold_angle

    def __init__(self, obj_id, contour, frame, timestamp):
        self.id = obj_id        
        self.contour = contour
        self.type = ObjectType.OBJECT
        self.roi = self.get_roi(frame)

        self.unseen = 0
        self.sp = StatePredictor(initial_pred_state=self.get_state())

        self.timestamps = [timestamp]
        self.state_history = [self.get_state()]
        self.predicted_state = self.predict_state()

        self.fallen = (False, None)

    def update_state(self, matching_obj):
        self.contour = matching_obj.contour
        self.roi = matching_obj.roi
        self.unseen = matching_obj.unseen
        
        if not self.type == ObjectType.HUMAN:
            self.type = matching_obj.type
        
        self.timestamps.append(matching_obj.timestamps[-1])
        if len(self.state_history) > ImageObject.STATE_HISTORY_MAX_LEN:
            self.state_history.pop(0)
            
        self.state_history.append(self.get_state())
        self.predicted_state = self.predict_state()

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
        return State(cm[0], cm[1], h, w, abs(angle))

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

    def detect_human(self, people_detector):
        roi = self.roi.copy()

        if people_detector.detect_human(roi)[0]:
            self.type = ObjectType.HUMAN
            return True
        else:
            self.TYPE = ObjectType.OBJECT
            return False
    
    def get_pose(self):
        x,y,h,w,angle = self.get_state().to_np_array()
        return ImageObject.calculate_pose(h, w, angle)
    
    @staticmethod
    def calculate_pose(h, w, angle):
        ratio = h / w
        if ratio > ImageObject.STANDING_THRESHOLD:
            pose = "STANDING"
        elif ratio > ImageObject.LYING_THRESHOLD:
            if angle > ImageObject.LYING_THRESHOLD_ANGLE:
                pose = "SITTING"
            else:
                pose = "LYING"
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
        self.predicted_state.draw(frame)

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
        predicted_state = self.predicted_state
        for obj in detected_objects:
            latest_state = obj.state_history[-1]
            area_ratio = float(predicted_state.get_area()) / latest_state.get_area()
            if (area_ratio < ImageObject.MATCH_AREA_TRESHOLD and 
                    area_ratio > 1.0/ImageObject.MATCH_AREA_TRESHOLD):
                candidates.append({
                    "mc_obj": obj, 
                    "dist_sq": predicted_state.dist_square_from(latest_state)
                })

        return candidates
        
    @staticmethod
    def merge_objects(objects: list, frame, timestamp):
        # convexhull, approxpoly
        
        if not objects:
            raise AttributeError('Cannot merge an empty list of ImageObjects')

        # Merge object contours
        merged_contours = np.concatenate([o.contour for o in objects])
        hull = cv2.convexHull(merged_contours, returnPoints=True)
        merged_object = ImageObject(0, hull, frame, timestamp)
        return merged_object
        
