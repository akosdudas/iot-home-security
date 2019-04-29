# Utility functions for fall detection

import cv2
import numpy as np
import matplotlib.pyplot as plt
from raspberry_sec.module.falldetector.detector.state_predictor import State

class StatePlotter:
    """ 
    Class for plotting State objects for debugging and documentation purposes
    """

    def __init__(self):
        self.fig = plt.figure()
        self.x = self.fig.add_subplot(2,2,1)
        self.y = self.fig.add_subplot(2,2,2)
        self.h2w = self.fig.add_subplot(2,2,3)
        self.angle = self.fig.add_subplot(2,2,4)

    def plot_states(self, states: list, color = 'blue'):
        self.x.plot([state.x for state in states], color=color, linewidth=1)
        self.y.plot([state.y for state in states], color=color, linewidth=1)
        self.h2w.plot([state.h / state.w for state in states], color=color, linewidth=1)
        self.angle.plot([state.angle for state in states], color=color, linewidth=1)
        plt.pause(0.001)

    def dismiss(self):
        plt.close(self.fig)
