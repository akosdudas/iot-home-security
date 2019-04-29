import cv2
import sys, os
import time
import datetime
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from raspberry_sec.module.falldetector.detector.falldetector import FallDetector
from raspberry_sec.module.falldetector.detector.utils import StatePlotter

def test_falldetector_algo(config, fps, video_file, show_frame=True):
    cap = cv2.VideoCapture(video_file)
    fd = FallDetector(config)

    frame_cnt = -1
    skip_nth = int(120 / fps)

    falls = set()

    while(1):
        ret, frame = cap.read()
        if not ret:
            break

        frame_cnt += 1

        if frame_cnt % skip_nth:
            continue

        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)


        start_time = datetime.datetime.now()
        for fall in fd.process_frame(frame, timestamp):
            falls.add(fall)
        end_time = datetime.datetime.now()

        delta = (end_time - start_time)

        if show_frame:
            #print(timestamp)
            fd.draw()
            cv2.imshow('frame', fd.frame)

            k = cv2.waitKey(1) & 0xff
            if k == 27:
                break
            # If b key is pressed, execute pass statement for possible breakpoint
            elif k == 66 or k == 98:
                pass
            # If d key is pressed, draw the state history of the selected object. Press c to continue
            elif k == 68 or k == 100:
                while True:
                    plotter = None

                    command = cv2.waitKey(1) & 0xff
                    if command == 67 or command == 99:
                        if not plotter is None:
                            plotter.dismiss()
                        break
                    elif command > 47 and command < 58:
                        plotter = StatePlotter()
                        plotter.plot_states(
                            fd.scene.objects[command - 48].state_history,
                            timestamps=fd.scene.objects[command - 48].timestamps
                        )
                    command = 255
            k = 255
    
    cap.release()
    cv2.destroyAllWindows()

    return falls

def test_performance(config, videos_folder, output_folder):
    scenarios = [ 'chute{}{}'.format('0' if i < 10 else '', str(i)) for i in range(1, 25) ]

    videos = [ 'cam{}'.format(str(i)) for i in range(1, 9)]

    fps_vals = [ 5, 8, 10, 12, 18, 24, 30 ]

    for scenario in scenarios:
        results = {}
        for video in videos:
            results[video] = {}
            for fps in fps_vals:
                print(scenario, video, fps)
                video_file = os.path.join(videos_folder, scenario, video + '.avi')  
                falls = test_falldetector_algo(config, fps, video_file, show_frame=False)
                results[video][str(fps)] = list(falls)
        results_file = os.path.join(output_folder, '{}.json'.format(scenario))
        with open(results_file, 'w') as f:
            json.dump(results, f)

if __name__ == '__main__':
    current_folder = os.path.dirname(__file__)
    config_file = os.path.join(current_folder, 'test_parameters.json')

    with open(config_file) as f:
        config = json.load(f)

    TEST = 'SINGLE'
    #TEST = 'PERFORMANCE'

    if TEST == 'SINGLE':
        scenario = 'chute01'
        cam = 'cam8'
        fps = 24

        test_falldetector_algo(
            config, 
            fps, 
            os.path.join(current_folder, 'dataset', scenario, '{}.avi'.format(cam))
        )
    elif TEST == 'PERFORMANCE':
        test_performance(
            config, 
            os.path.join(current_folder, 'dataset'),
            os.path.join(current_folder, 'results')
        )