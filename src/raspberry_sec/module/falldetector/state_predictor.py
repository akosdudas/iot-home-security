import cv2
import numpy as np
import matplotlib.pyplot as plt
import operator

class State:
    STATE_VARS = ['x', 'y', 'h', 'w', 'angle']
    DRAWING_COLORS = {
        'cm': (0,0,255),
        'angle_line': (0,255,0),
        'bounding_rect': (255,0,0)
    }
    ANGLE_LINE_LENGTH = 50

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

    def draw(self, frame, rect_color = None):
        if rect_color == None:
            rect_color = State.DRAWING_COLORS['bounding_rect']

        # Draw center of mass
        cv2.circle(frame, (int(self.x), int(self.y)), 2, State.DRAWING_COLORS['cm'], 2)
        # Draw angle line
        p1 = (
            int(self.x - State.ANGLE_LINE_LENGTH/2 * np.cos(self.angle)), 
            int(self.y + State.ANGLE_LINE_LENGTH/2 * np.sin(self.angle))
        )
        p2 = (
            int(self.x + State.ANGLE_LINE_LENGTH/2 * np.cos(self.angle)), 
            int(self.y - State.ANGLE_LINE_LENGTH/2 * np.sin(self.angle))
        )
        cv2.line(frame, p1, p2, State.DRAWING_COLORS['angle_line'], 1)
        # Draw bounding rectangle
        cv2.rectangle(
            frame,
            (int(self.x - self.w/2.0), int(self.y - self.h/2.0)),
            (int(self.x + self.w/2.0), int(self.y + self.h/2.0)),
            color = rect_color,
            thickness = 2
        )
        

class StatePredictor:
    STATE_VECTOR_LEN = 10
    MEAS_VECTOR_LEN = 5
    def __init__(self, initial_pred_state: State = None):

        self.kalman = cv2.KalmanFilter(
            StatePredictor.STATE_VECTOR_LEN, 
            StatePredictor.MEAS_VECTOR_LEN
        )

        self.kalman.measurementMatrix = np.array(
            [[1,0,0,0,0,0,0,0,0,0],
             [0,1,0,0,0,0,0,0,0,0],
             [0,0,1,0,0,0,0,0,0,0],
             [0,0,0,1,0,0,0,0,0,0],
             [0,0,0,0,1,0,0,0,0,0]], np.float32
        )

        self.kalman.transitionMatrix = np.array(
            [[1,0,0,0,0,1,0,0,0,0],
             [0,1,0,0,0,0,1,0,0,0],
             [0,0,1,0,0,0,0,0,0,0],
             [0,0,0,1,0,0,0,0,0,0],
             [0,0,0,0,1,0,0,0,0,1],
             [0,0,0,0,0,1,0,0,0,0],
             [0,0,0,0,0,0,1,0,0,0],
             [0,0,0,0,0,0,0,1,0,0],
             [0,0,0,0,0,0,0,0,1,0],
             [0,0,0,0,0,0,0,0,0,1]], np.float32
        )

        self.kalman.processNoiseCov = np.eye(
            StatePredictor.STATE_VECTOR_LEN, dtype=np.float32
        ) * 0.03

        if initial_pred_state == None:
            self.initial_pred_state = State.from_np_array(
                np.zeros(StatePredictor.MEAS_VECTOR_LEN)
            )
        else:
            self.initial_pred_state = initial_pred_state

    def predict_state(self, state):
        self.kalman.correct((state - self.initial_pred_state).to_np_array())
        prediction = State.from_np_array(self.kalman.predict()) + self.initial_pred_state
        return prediction

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
    arr = np.ones(StatePredictor.MEAS_VECTOR_LEN, dtype=np.float32) * coords[0]
    sp = StatePredictor(
        State.from_np_array(arr)
        )
    prs = [0]
    for coor in coords:
        pr = sp.predict_state(
            State.from_np_array(np.ones(StatePredictor.MEAS_VECTOR_LEN, np.float32) * coor)
            ).to_np_array()
        prs.append(pr[0])
    plt.plot(coords)
    plt.plot(prs)
    plt.show()
    pass