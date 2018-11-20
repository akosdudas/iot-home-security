import cv2
import numpy as np
import matplotlib.pyplot as plt

class State:
    def __init__(self, x, y):#, h, w, vRatio, angle):
        self.__dict__.update(locals())
    
        

class StatePredictor:
    def __init__(self):
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
        ) * 0.05

    def predict_state(self, state):
        self.kalman.correct(
            np.array([np.float32(state.x), np.float32(state.y)], np.float32)
        )
        prediction = self.kalman.predict()
        return prediction

if __name__ == '__main__':
    coords = [1,7,10,44,-1,3,2,1,0,5,123,12,0,1]
    sp = StatePredictor()
    prs = []
    for coor in coords:
        pr = sp.predict_state(State(coor, coor))
        prs.append((pr[0], pr[1]))
    prs = [a[0] for a in prs]
    plt.plot(prs)
    plt.plot(coords)
    plt.show()
    pass