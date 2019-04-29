import numpy as np 
import cv2
import imutils

from enum import Enum
from types import SimpleNamespace

from raspberry_sec.module.falldetector.detector.state_predictor import State, StatePredictor

class ObjectType(Enum):
    """
    Enum class for ImageObject types
    """
    OBJECT = 0
    HUMAN = 1

class ImageObject:
    """
    Class for representing and tracking objects in a video stream
    """

    PADDING = 30
    MATCH_AREA_TRESHOLD = 2
    STATE_HISTORY_MAX_LEN = 500
    STANDING_THRESHOLD = 1.5
    LYING_THRESHOLD = 0.5
    LYING_THRESHOLD_ANGLE = np.pi / 4

    @staticmethod
    def configure(padding, match_area_threshold, state_history_max_len,
                  standing_threshold, lying_threshold, lying_threshold_angle):
        """
        Function for configuring ImageObject class parameters
        :param padding: Padding to be added to the enclosing rectangle
             of the object to form it's region of interest
        :param match_area_threshold: The area threshold for matching objects
        :param state_history_max_len: The maximum length of the object
            state history
        :param standing_threshold: The height/width ratio over which the 
            object is considered to be standing
        :param lying_threshold: The height/width ratio under which the 
            object is considered to be lying
        :param lying_threshold_angle: If the height/width ratio of the 
            object falls between standing_threshold and lying_threshold,
            consider the object lying if the angle of the object is 
            under lying_threshold_angle
        """
        ImageObject.PADDING = padding
        ImageObject.MATCH_AREA_TRESHOLD = match_area_threshold
        ImageObject.STATE_HISTORY_MAX_LEN = state_history_max_len
        ImageObject.STANDING_THRESHOLD = standing_threshold
        ImageObject.LYING_THRESHOLD = lying_threshold
        ImageObject.LYING_THRESHOLD_ANGLE = lying_threshold_angle

    def __init__(self, obj_id, contour, frame, timestamp):
        """
        Constructor
        :param obj_id: Object id
        :param contour: Array representing the contours of the object
        :param frame: The video frame the object was found on
        :param timestamp: The timestamp of the video frame
        """
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
        """
        Update the state of the object based on a matching object found on the next frame
        :param matching_obj: Matching object found on the next frame
        """
        self.contour = matching_obj.contour
        self.roi = matching_obj.roi
        self.unseen = matching_obj.unseen
        
        if not self.type == ObjectType.HUMAN:
            self.type = matching_obj.type
        
        self.timestamps.append(matching_obj.timestamps[-1])
        # Pop the first element of the state history list if it exceeded its 
        # maximum length
        if len(self.state_history) > ImageObject.STATE_HISTORY_MAX_LEN:
            self.state_history.pop(0)
            
        self.state_history.append(self.get_state())
        self.predicted_state = self.predict_state()

    def predict_state(self):
        """
        Run state prediction for the object
        :return: predicted state
        """
        return self.sp.predict_state(self.get_state())

    def get_state(self):
        """
        Get the object's state
        :return: State
        """
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
        """
        Get the region of interest of the object
        :param frame: The video frame the object was found on
        :return: ROI
        """
        x,y,u,v = self.get_rect()
        xR = max(0, x - ImageObject.PADDING)
        yR = max(0, y - ImageObject.PADDING)
        uR = min(frame.shape[1] - 1, u + ImageObject.PADDING)
        vR = min(frame.shape[0] - 1, v + ImageObject.PADDING)
        return frame[yR:vR, xR:uR]

    def get_area(self):
        """
        Get the area enclosed by the contour of the object
        :return: Area of the object in pixels
        """
        return cv2.contourArea(self.contour)

    def get_rect_area(self):
        """
        Get the area of the object's enclosing rectangle
        :return: Area of the enclosing rectangle in pixels
        """
        x,y,w,h = self.get_rect_wh()
        return w*h

    def get_center_of_mass(self):
        """
        Get the object's center of mass
        :return: Pixel coordinates of center of mass
        """
        ellipse = self.get_ellipse()
        if not ellipse:
            return None
        
        return ellipse[0]

    def get_rect_wh(self):
        """
        Get the object's enclosing rectangle in a position&sizes format
        :return: (x,y,w,h)
        """
        return cv2.boundingRect(self.contour)

    def get_rect(self):
        """
        Get the object's enclosing rectangle by its corners
        :return: The 4 corners of the enclosing rectangle
        """
        x,y,w,h = self.get_rect_wh()
        return (x, y, x + w, y + h)


    def get_ellipse(self):
        """
        Get the ellipse that can be fit to the object's contours
        :return: Fitting ellipse
        """
        try:
            return cv2.fitEllipse(self.contour)
        except:
            # Ellipse can only be fit to contours with 5 or more points 
            return None

    def get_angle(self):
        """
        Get the angle of the object
        :return: angle in radians 
        """
        ellipse = self.get_ellipse()
        if ellipse:
            # The 3rd parameter of the ellipse is the angle of the ellipse
            return (90 - ellipse[2])/180*np.pi
        else:
            # If an ellipse could not be fit, return none instead of the angle
            return None

    def get_line_repr(self):
        """
        Get the line that can be draw over the object by returning the major axis of
        the fitting ellipse of the object
        :return: ((x0, y0), (x1, y1)) starting and ending points of the line
        """
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
        """
        Detect human figure in the ROI of the object
        :return: True if a human figure was detected, False otherwise
        """ 
        roi = self.roi.copy()

        if people_detector.detect_human(roi)[0]:
            self.type = ObjectType.HUMAN
            return True
        else:
            self.TYPE = ObjectType.OBJECT
            return False
    
    def get_pose(self):
        """
        Get the current pose of the object
        :return: 'STANDING', 'SITTING' or 'LYING'
        """
        x,y,h,w,angle = self.get_state().to_np_array()
        return ImageObject.calculate_pose(h, w, angle)
    
    @staticmethod
    def calculate_pose(h, w, angle):
        """
        Calculate the pose of an object state based on its height, widht and angle
        :param h: height
        :param w: width
        :param angle: angle
        :return: 'STANDING', 'SITTING' or 'LYING'
        """
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
        """
        Draw the object on the video frame specified
        :param frame: Video frame
        """
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
        """
        Calculate the square of the object's distance from another object
        :param other: ImageObject
        :return: Square of the distance of the objects
        """
        cm_self = self.get_center_of_mass()
        cm_other = other.get_center_of_mass()

        x = cm_self[0] - cm_other[0]
        y = cm_self[1] - cm_other[1]

        return x*x + y*y

    def contains(self, other):
        """
        Determine if the object contains inside it an other object specified
        :param other: ImageObject
        :return: True if the object contains the other object specified, False otherwise
        """
        cm_other = other.get_center_of_mass()
        x,y,u,v = self.get_rect()
        return x < cm_other[0] < u and y < cm_other[1] < v 

    def find_match_candidates(self, detected_objects: list):
        """
        Find objects in the list specified that could match self
        :param detected_objects: List of the objects detected that are used for
                searching for matches
        :return: Dictionary of match candidates and the square of their distance
        """
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
        """
        Merge the contours of a list of objects by fitting a convex hull over them
        :param objects: List of ImageObjects
        :param frame: The video frame the objects were detected on
        :param timestamp: The timestamp of the video frame in milliseconds
        """
        # convexhull, approxpoly
        
        if not objects:
            raise AttributeError('Cannot merge an empty list of ImageObjects')

        # Merge object contours
        merged_contours = np.concatenate([o.contour for o in objects])
        hull = cv2.convexHull(merged_contours, returnPoints=True)
        merged_object = ImageObject(0, hull, frame, timestamp)
        return merged_object
        
