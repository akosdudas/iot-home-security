import numpy as np
from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject

def detect_fall_event(obj: ImageObject):
    stabilize_interval_ms = 1000
    fall_interval_ms = 1000

    if not is_final_position_lying(obj):
        return (False, None)

    if not has_pose_stabilized(obj, stabilize_interval_ms):
        return (False, None)

    fallen, timestamp = obj.fallen
    if fallen:
        return (fallen, timestamp)

    (fall_occured, timestamp) = has_fall_occured(obj, stabilize_interval_ms, fall_interval_ms)

    return (fall_occured, timestamp)

def is_final_position_lying(obj: ImageObject):
    if obj.get_pose() == "LYING":
        return True
    else:
        return False

def get_interval_start_index(obj: ImageObject, time_interval_ms):
    interval_end = obj.timestamps[-1]

    for i, ts in reversed(list(enumerate(obj.timestamps))):
        if interval_end - ts >= time_interval_ms:
            return i
    else:
        return 0

def has_pose_stabilized(obj: ImageObject, time_interval_ms=500):
    tolerance = {
        "pos": 20,
        "size": 20,
        "angle": 0.1
    }

    interval_end = obj.timestamps[-1]

    # If the time difference between the first and latest occurence of the
    # object is smaller than the time interval needed for the pose to be 
    # considered stabilized, return False
    if interval_end - obj.timestamps[0] < time_interval_ms:
        return False

    interval_start_index = get_interval_start_index(obj, time_interval_ms)

    # Return True, if all state variables has stabilized
    if not has_state_variable_stabilized(obj, "x", interval_start_index, tolerance["pos"]):
        return False
    if not has_state_variable_stabilized(obj, "y", interval_start_index, tolerance["pos"]):
        return False
    if not has_state_variable_stabilized(obj, "h", interval_start_index, tolerance["size"]):
        return False
    if not has_state_variable_stabilized(obj, "w", interval_start_index, tolerance["size"]):
        return False
    if not has_state_variable_stabilized(obj, "angle", interval_start_index, tolerance["angle"]):
        return False
    return True

def has_state_variable_stabilized(obj: ImageObject, state_var_name, interval_start_index, tolerance):
    # Calculate standard deviations of the state variables 
    # in the given interval
    var = [state.__dict__[state_var_name] for state in obj.state_history[interval_start_index:]]
    dev = np.std(var)
    if dev > tolerance:
        return False
    else: 
        return True

def has_fall_occured(obj: ImageObject, stabilized_interval_ms=500, time_interval_ms=1000):
    stabilized_interval_start_index = get_interval_start_index(obj, stabilized_interval_ms)
    fall_interval_start_index = get_interval_start_index(obj, time_interval_ms + stabilized_interval_ms)

    states = [state for state in obj.state_history[fall_interval_start_index:stabilized_interval_start_index]]
    for state in states:
        pose = ImageObject.calculate_pose(state.h, state.w, state.angle)
        if pose == 'STANDING':
            return (True, obj.timestamps[stabilized_interval_start_index])
    else:
        return (False, None)
