import cv2
import numpy as np
import matplotlib.pyplot as plt
import operator

class State:
    STATE_VARS = ['x', 'y']#, h, w, vRatio, angle]
    
    def __init__(self, *args):
        for i, state_var in enumerate(State.STATE_VARS):
            self.__setattr__(state_var, args[i])
    
    def to_np_array(self):
        return np.array(
            [np.float32(self.__dict__[state_var]) for state_var in State.STATE_VARS], np.float32
        )

    @staticmethod
    def from_np_array(input_array):
        return State(*[state_var for state_var in input_array])

    def __add__(self, other):
        if type(other) is State:
            return self.__add_sub_helper__(other, operator.add)
            
    def __sub__(self, other):
        if type(other) is State:
            return self.__add_sub_helper__(other, operator.sub)

    def __add_sub_helper__(self, other, op):
        arr1 = self.to_np_array()
        arr2 = other.to_np_array()
        arr_out = np.array(
            [op(var1, var2) for (var1, var2) in zip(arr1, arr2)], np.float32
        )
        return State.from_np_array(arr_out)

class StatePredictor:
    def __init__(self, initial_pred_state: State = State(0,0)):
        self.kalman = cv2.KalmanFilter(4,2)
        self.kalman.measurementMatrix = np.array(
            [[1,0,0,0],
             [0,1,0,0]], np.float32
        )
        self.kalman.transitionMatrix = np.array(
            [[1,0,1,0],
             [0,1,0,1],
             [0,0,1,0],
             [0,0,0,1]], np.float32
        )
        self.kalman.processNoiseCov = np.array(
            [[1,0,0,0],
             [0,1,0,0],
             [0,0,1,0],
             [0,0,0,1]], np.float32
        ) * 0.03

        self.initial_pred_state = initial_pred_state

    def predict_state(self, state):
        self.kalman.correct((state - self.initial_pred_state).to_np_array())
        prediction = State.from_np_array(self.kalman.predict()) + self.initial_pred_state
        return prediction.to_np_array()

if __name__ == '__main__':

    if False:
        state = State(10, 20)
        state2 = State(11.13, 12.14)
        state3 = state + state2
        state4 = state - state2
        arr = state2.to_np_array()
        state5 = State.from_np_array(arr)

    import random as rand
    coords = [val + rand.gauss(0, 40) for val in range(100, 300)]
    arr = np.array([coords[0], coords[0]], np.float32)
    sp = StatePredictor(
        State.from_np_array(arr)
        )
    prs = [(0, 0)]
    for coor in coords:
        pr = sp.predict_state(
            State.from_np_array(np.array([coor, coor], np.float32))
            )
        prs.append((pr[0], pr[1]))
    prs = [a[0] for a in prs]
    plt.plot(coords)
    plt.plot(prs)
    plt.show()
    pass