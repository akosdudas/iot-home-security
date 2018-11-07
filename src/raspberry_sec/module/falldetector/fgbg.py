# Foreground extractor utlities for fall detection
import cv2

class BS:
    def __init__(self, bs, learnrate=[-1, -1]):
        self.bs = bs
        self.fgmask = None
        self.learnrate = learnrate

    def get_mask(self, frame):
        if self.fgmask is None:
            self.fgmask = self.bs.apply(frame, self.fgmask, self.learnrate[0])
        else:
            self.fgmask = self.bs.apply(frame, self.fgmask, self.learnrate[1])
        return self.fgmask

    def denoise_mask(self):
        fgmask = self.fgmask.copy()        
        thresh = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
        thresh = cv2.dilate(thresh, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)), iterations=1)
        thresh = cv2.erode(thresh, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)), iterations=2)
        return thresh

class GSOC(BS):
    def __init__(self):
        fgbg = cv2.bgsegm.createBackgroundSubtractorGSOC()
        super().__init__(fgbg, [0, 0.001])

class MOG2(BS):
    def __init__(self):
        fgbg = cv2.createBackgroundSubtractorMOG2(500, 16, 0)
        super().__init__(fgbg, [0, 0.001])

class CNT(BS):
    def __init__(self):
        fgbg = cv2.bgsegm.createBackgroundSubtractorCNT()#15, True, 15*60, False)
        super().__init__(fgbg)