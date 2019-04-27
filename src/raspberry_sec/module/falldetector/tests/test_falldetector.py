import cv2
import sys, os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from raspberry_sec.module.falldetector.detector.falldetector import FallDetector
from raspberry_sec.module.falldetector.detector.utils import StatePlotter

def test_falldetector_algo(fps, video_file, show_frame=True):
    cap = cv2.VideoCapture(video_file)
    fd = FallDetector()

    print(cap.get(cv2.CAP_PROP_FPS))

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

        for fall in fd.process_frame(frame, timestamp):
            falls.add(fall)

        if show_frame:
            print(timestamp)
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
                        plotter.plot_states(fd.scene.objects[command - 48].state_history)
                    command = 255
            k = 255
    
    cap.release()
    cv2.destroyAllWindows()

    return falls

def test_performance(videos_folder, output_folder):
    scenarios = [ 'chute{}{}'.format('0' if i < 10 else '', str(i)) for i in range(1, 25) ]

    videos = [ 'cam{}'.format(str(i)) for i in range(1, 9)]

    fps_vals = [
        24
    ]

    for fps in fps_vals:    
        for scenario in scenarios:
            for video in videos:
                video_file = os.path.join(videos_folder, scenario, video + '.avi')
                falls = test_falldetector_algo(fps, video_file, show_frame=True)
                results_file = os.path.join(output_folder, 'fps-{}-{}.txt'.format(str(fps), scenario))
                with open(results_file, 'a+') as f:
                    f.write('{} - {}\n'.format(video, str(falls)))

if __name__ == '__main__':
    test_performance(
        '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/tests/dataset/dataset',
        '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/tests/results'
    )