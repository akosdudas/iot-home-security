import numpy as np
from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject

def detect_fall_event(obj: ImageObject):
    stabilize_interval_ms = 1000
    fall_interval_ms = 1000

    if not is_final_position_lying(obj):
        return (False, )

    if not has_pose_stabilized(obj, stabilize_interval_ms):
        return (False, )

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

def has_fall_occured2(obj: ImageObject, time_interval_ms=2000):
    interval_start_index = get_interval_start_index(obj, time_interval_ms)
    fps = 1000 / (obj.timestamps[-1] - obj.timestamps[-2])
    angles = [state.angle for state in obj.state_history[interval_start_index:]]
    smoothed = smooth(np.array(angles), window_len=int((fps + 1)/4), window='flat')
    grad = np.gradient(smoothed)
    pos_neg = []
    for g in smoothed_grad:
        if abs(g) < 0:
            pos_neg.append(0)
        elif g < 0:
            pos_neg.append(-1)
        elif g > 0:
            pos_neg.append(1)

    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(angles)
    plt.plot(smoothed)
    plt.plot(grad)
    plt.plot(pos_neg)
    plt.pause(0.001)
    return (False, None)

def smooth(x,window_len=5,window='flat'):
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
    if window_len<3:
        return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')
    y=np.convolve(w/w.sum(),s,mode='valid')
    return y    