import numpy as np
import cv2
import imutils

from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject
from raspberry_sec.module.falldetector.detector.scene import Scene
from raspberry_sec.module.falldetector.detector.fgbg import BS, CNT, GSOC, MOG2
from raspberry_sec.module.falldetector.detector.people_detector import HOGDetector, MobileNetSSD
from raspberry_sec.module.falldetector.detector.fall_event_detector import FallEventDetector

class FallDetector():

    def __init__(self, parameters: dict):
        
        self.obj_min_area = parameters['obj_min_area']
        self.obj_max_area = parameters['obj_max_area']
        
        fgbg_algo = parameters['background_subtractor_algo']
        fgbg_params = parameters['background_subtractor_parameters']
        if fgbg_algo == 'CNT':
            self.bs = CNT(fgbg_params)
        elif fgbg_algo == 'MOG2':
            self.bs = MOG2(fgbg_params)
        elif fgbg_algo == 'GSOC':
            self.bs = GSOC(fgbg_params)
        else:
            raise AttributeError('Incorrect background subtraction algorithm')
        
        people_detector_algo = parameters['people_detector_algo']
        people_detector_parameters = parameters['people_detector_parameters']
        if people_detector_algo == 'HOG':
            self.people_detector = HOGDetector(people_detector_parameters)
        elif people_detector_algo == 'MobileNetSSD':
            self.people_detector = MobileNetSSD(people_detector_parameters)
        else: 
            raise AttributeError('Incorrect people detector algorithm')
        
        ImageObject.configure(
            parameters['obj_padding'],
            parameters['obj_match_area_threshold'],
            parameters['obj_state_history_max_len'],
            parameters['pose_ratios']['standing_threshold'],
            parameters['pose_ratios']['lying_threshold'],
            parameters['pose_ratios']['lying_threshold_angle']        
        )

        self.scene = Scene(parameters['obj_expiration'])

        fall_event_detector_params = parameters['fall_event_detector_parameters']
        self.fall_event_detector = FallEventDetector(
            fall_event_detector_params['stabilized_interval_ms'],
            fall_event_detector_params['fall_interval_ms'],
            fall_event_detector_params['stabilized_tolerance']
        )

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
            if obj.get_area() < self.obj_min_area:
                continue
            if obj.get_area() > self.obj_max_area:
                continue
            obj.detect_human(self.people_detector)
            objects.append(obj)
        self.scene.update_objects(objects, self.frame, timestamp)

        falls = []
        human_ids = self.scene.get_human_objects()
        for human in human_ids:
            fall_occured, timestamp = self.fall_event_detector.detect_fall_event(
                self.scene.objects[human]
            )
            self.scene.objects[human].fallen = (fall_occured, timestamp)
            if fall_occured:
                falls.append(timestamp)
        
        return falls

    def draw(self):
        # If there were no processed frames, drawing is not possible
        if self.frame is None:
            return
        for i, o in self.scene.objects.items():
            o.draw(self.frame)

