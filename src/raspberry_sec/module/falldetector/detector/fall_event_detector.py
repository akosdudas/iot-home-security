import numpy as np
from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject

class FallEventDetector:
    def __init__(self, stabilize_interval_ms, fall_interval_ms, tolerance: dict):
        self.stabilize_interval_ms = stabilize_interval_ms
        self.fall_interval_ms = fall_interval_ms
        self.tolerance = tolerance

    def detect_fall_event(self, obj: ImageObject):
        if not FallEventDetector.is_final_position_lying(obj):
            return (False, None)

        if not self.has_pose_stabilized(obj):
            return (False, None)

        fallen, timestamp = obj.fallen
        if fallen:
            return (fallen, timestamp)

        (fall_occured, timestamp) = self.has_fall_occured(obj)

        return (fall_occured, timestamp)

    @staticmethod
    def is_final_position_lying(obj: ImageObject):
        if obj.get_pose() == "LYING":
            return True
        else:
            return False

    @staticmethod
    def get_interval_start_index(obj: ImageObject, time_interval_ms):
        interval_end = obj.timestamps[-1]

        for i, ts in reversed(list(enumerate(obj.timestamps))):
            if interval_end - ts >= time_interval_ms:
                return i
        else:
            return 0

    def has_pose_stabilized(self, obj: ImageObject):
        time_interval_ms = self.stabilize_interval_ms
        tolerance = self.tolerance

        interval_end = obj.timestamps[-1]

        # If the time difference between the first and latest occurence of the
        # object is smaller than the time interval needed for the pose to be 
        # considered stabilized, return False
        if interval_end - obj.timestamps[0] < time_interval_ms:
            return False

        interval_start_index = FallEventDetector.get_interval_start_index(
            obj, time_interval_ms
        )

        # Return True, if all state variables has stabilized
        if not FallEventDetector.has_state_variable_stabilized(
                obj, "x", interval_start_index, tolerance["pos"]):
            return False
        if not FallEventDetector.has_state_variable_stabilized(
                obj, "y", interval_start_index, tolerance["pos"]):
            return False
        if not FallEventDetector.has_state_variable_stabilized(
                obj, "h", interval_start_index, tolerance["size"]):
            return False
        if not FallEventDetector.has_state_variable_stabilized(
                obj, "w", interval_start_index, tolerance["size"]):
            return False
        if not FallEventDetector.has_state_variable_stabilized(
                obj, "angle", interval_start_index, tolerance["angle"]):
            return False
        return True

    @staticmethod
    def has_state_variable_stabilized(obj: ImageObject, state_var_name, interval_start_index, tolerance):
        # Calculate standard deviations of the state variables 
        # in the given interval
        var = [
            state.__dict__[state_var_name] for state in 
                obj.state_history[interval_start_index:]
        ]
        dev = np.std(var)
        if dev > tolerance:
            return False
        else: 
            return True

    def has_fall_occured(self, obj: ImageObject):
        stabilized_interval_start_index = FallEventDetector.get_interval_start_index(
            obj, self.stabilize_interval_ms
        )
        fall_interval_start_index = FallEventDetector.get_interval_start_index(
            obj, self.fall_interval_ms + self.stabilize_interval_ms
        )

        states = [
            state for state in 
                obj.state_history[fall_interval_start_index:stabilized_interval_start_index]
        ]
        for state in states:
            pose = ImageObject.calculate_pose(state.h, state.w, state.angle)
            if pose == 'STANDING':
                return (True, obj.timestamps[stabilized_interval_start_index])
        else:
            return (False, None)

