import numpy as np
from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject

class FallEventDetector:
    """
    Class for detecting fall events in an ImageObject state history
    :param stabilize_interval_ms: The time interval in which the objects state
            variables has to stay stable for the object to be considered stabilized
    :param fall_interval_ms: The time interval before the state variables has 
            stabilized in which the state history is examined for a fall event
    :param tolerance: The tolerance of the standard deviations of the state variables
            when examining of they are stabilized
    """
    def __init__(self, stabilize_interval_ms, fall_interval_ms, tolerance: dict):
        self.stabilize_interval_ms = stabilize_interval_ms
        self.fall_interval_ms = fall_interval_ms
        self.tolerance = tolerance

    def detect_fall_event(self, obj: ImageObject):
        """
        Detect a fall event in an image object state history
        :param obj: ImageObject
        :return: (bool, time_ms) bool is True if a fall has been detected,
                False otherwise. time_ms is the timestamp of the fall if 
                a fall has occurred, None otherwise
        """
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
        """
        Determine if the final position of the object is LYING
        :param obj: ImageObject
        :return: True if LYING, False otherwise
        """
        if obj.get_pose() == "LYING":
            return True
        else:
            return False

    @staticmethod
    def get_interval_start_index(obj: ImageObject, time_interval_ms):
        """
        Get the starting index of a given time interval in the object state history list
        :param obj: ImageObject
        :param time_interval_ms: Time interval in milliseconds
        :return: The starting index of the time interval in the object state history list
        """
        interval_end = obj.timestamps[-1]

        for i, ts in reversed(list(enumerate(obj.timestamps))):
            if interval_end - ts >= time_interval_ms:
                return i
        else:
            return 0

    def has_pose_stabilized(self, obj: ImageObject):
        """
        Determine if the state of an ImageObject has stabilized
        :param obj: ImageObject
        :return: True if stabilized, False otherwise
        """
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
        """
        Determine if a single state variable of an ImageObject has stabilized
        :param obj: ImageObject
        :param state_var_name: The name of the state variable examined
        :param interval_start_index: The starting index of the time interval in which
                the state variable is examined
        :param tolerance: The tolerance value of the std deviation of the state variable
                in the given time interval
        :return: True if the state variable has stabilized, False otherwise
        """
        # Calculate standard deviations of the state variables 
        # in the given interval
        var = [
            state.__dict__[state_var_name] for state in 
                obj.state_history[interval_start_index:]
        ]
        dev = np.std(var)
        
        # If the deviation is larger than the tolerance, the state variable
        # has not stabilized
        if dev > tolerance:
            return False
        else: 
            return True

    def has_fall_occured(self, obj: ImageObject):
        """
        Detect fall event in the state history of an image object
        :param obj: ImageObject
        :return: (bool, time_ms) bool is True if a fall has been detected,
                False otherwise. time_ms is the timestamp of the fall if 
                a fall has occurred, None otherwise
        """

        # Get the latest index of the time interval to be examined
        stabilized_interval_start_index = FallEventDetector.get_interval_start_index(
            obj, self.stabilize_interval_ms
        )
        # Get the starting index of the time interval to be examined
        fall_interval_start_index = FallEventDetector.get_interval_start_index(
            obj, self.fall_interval_ms + self.stabilize_interval_ms
        )

        # Get the states of the given time interval of the object state history
        states = [
            state for state in 
                obj.state_history[fall_interval_start_index:stabilized_interval_start_index]
        ]

        # If any STANDING positions have been detected in the given time interval,
        # a fall event has occured
        for state in states:
            pose = ImageObject.calculate_pose(state.h, state.w, state.angle)
            if pose == 'STANDING':
                return (True, obj.timestamps[stabilized_interval_start_index])
        # No STANDING positions have been found, no fall event has occured
        else:
            return (False, None)

