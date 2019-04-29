# Foreground extractor utlities for fall detection
import cv2

class BS:
    def __init__(self, bs, params):
        self.bs = bs
        self.fgmask = None
        self.learnrate = params['learnrate']
        self.learnrate_initial = params['learnrate_initial']
        self.morph_open_ellipse_size = params['morph_open_ellipse_size']
        self.dilate_ellipse_size = params['dilate_ellipse_size']
        self.dilate_iterations = params['dilate_iterations']
        self.erode_ellipse_size = params['erode_ellipse_size']
        self.erode_iterations = params['erode_iterations']

    def get_mask(self, frame):
        if self.fgmask is None:
            self.fgmask = self.bs.apply(frame, self.fgmask, self.learnrate_initial)
        else:
            self.fgmask = self.bs.apply(frame, self.fgmask, self.learnrate)
        return self.fgmask

    def denoise_mask(self):
        fgmask = self.fgmask.copy()        
        thresh = cv2.morphologyEx(
            fgmask, 
            cv2.MORPH_OPEN, 
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                (self.morph_open_ellipse_size, self.morph_open_ellipse_size)
            )
        )

        thresh = cv2.dilate(
            thresh, 
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                (self.dilate_ellipse_size, self.dilate_ellipse_size)
            ), 
            iterations=self.dilate_iterations
        )

        thresh = cv2.erode(
            thresh, 
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                (self.erode_ellipse_size, self.erode_ellipse_size)
            ), 
            iterations=self.erode_iterations
        )
        return thresh

class GSOC(BS):
    def __init__(self, params):
        fgbg = cv2.bgsegm.createBackgroundSubtractorGSOC()
        super().__init__(fgbg, params)

class MOG2(BS):
    def __init__(self, params):
        fgbg = cv2.createBackgroundSubtractorMOG2(500, 16, 0)
        super().__init__(fgbg, params)

class CNT(BS):
    def __init__(self, params):
        fgbg = cv2.bgsegm.createBackgroundSubtractorCNT()#15, True, 15*60, False)
        super().__init__(fgbg, params)