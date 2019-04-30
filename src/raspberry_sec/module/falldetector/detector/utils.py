# Utility functions for fall detection

import cv2
import numpy as np
import matplotlib.pyplot as plt
from raspberry_sec.module.falldetector.detector.state_predictor import State
from raspberry_sec.module.falldetector.detector.object_tracker import ImageObject

class StatePlotter:
    """ 
    Class for plotting State objects for debugging and documentation purposes
    """

    def __init__(self):
        """
        Constructor
        """
        self.fig = plt.figure(figsize=(12, 8))
        self.x = self.fig.add_subplot(2,2,1)
        self.x.set_title('x [px]')
        self.y = self.fig.add_subplot(2,2,2)
        self.y.set_title('y [px]')
        self.h2w = self.fig.add_subplot(2,2,3)
        self.h2w.set_title('height/width')
        self.angle = self.fig.add_subplot(2,2,4)
        self.angle.set_title('angle [rad]')

    def plot_states(self, states: list, timestamps=None, color = 'blue'):
        """
        Plot a list of states
        :param states: The list of states to be plotted
        :param timestamps: The timestamps of the states
        :param color: The color used to plot the states
        """
        if timestamps:
            x_axis = timestamps
        else:
            x_axis = range(len(states))
        self.x.plot(x_axis, [state.x for state in states], color=color, linewidth=1)
        self.y.plot(x_axis, [state.y for state in states], color=color, linewidth=1)
        self.h2w.plot(x_axis, [state.h / state.w for state in states], color=color, linewidth=1)
        self.h2w.plot(x_axis, [ImageObject.STANDING_THRESHOLD for state in states], color='red', linewidth=1, linestyle='dashed')
        self.h2w.plot(x_axis, [ImageObject.LYING_THRESHOLD for state in states], color='green', linewidth=1, linestyle='dashed')
        self.angle.plot(x_axis, [state.angle for state in states], color=color, linewidth=1)
        self.angle.plot(x_axis, [ImageObject.LYING_THRESHOLD_ANGLE for state in states], color='red', linewidth=1, linestyle='dashed')
        plt.pause(0.001)

    def dismiss(self):
        """
        Dismiss figure
        """
        plt.close(self.fig)
