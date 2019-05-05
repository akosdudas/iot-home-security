import os
import json
import csv

def generate_summary(results_folder, ground_truth_file, output_file):
    gt = None
    with open(labels) as f:
        gt = json.load(f)

    result_files = sorted([f for f in os.listdir(results_folder) if f.endswith('.json')])

    results = []

    for rf in result_files:
        with open(os.path.join(results_folder, rf)) as f:
            res = json.load(f)
        scenario = os.path.splitext(rf)[0]
        try:
            results.append({
                "name": scenario,
                "results": generate_results_for_scenario(gt[scenario], res)
            })
        except:
            pass
    
    with open(output_file, 'w') as csv_file:
        writer = csv.writer(csv_file)
        
        for result in results:
            falls = result["results"]["stats"]["falls"]
            writer.writerow([
                'Scenario', 
                result["name"], 
                'Falls', 
                ', '.join([ 
                    '{} - {}'.format(str(int(fall["fall_started_after"])), str(int(fall["fall_ended_before"]))) for fall in falls
                ])
            ])
            header = ['FPS'] + [ 'cam{}'.format(i) for i in range(1, 9) ] + [ 'True Positives', 'False Positives', 'False Negatives']
            writer.writerow(header)
            for fps in result["results"]["results"].keys():
                row = [fps] + fps_to_csv_row(result["results"]["results"][fps])
                writer.writerow(row)

def fps_to_csv_row(fps):
    row = []
    for cam in sorted(fps["falls"].keys()):
        row.append(', '.join([str(int(fall)) for fall in fps["falls"][cam]]))
    row.append(fps["true_positive"])
    row.append(fps["false_positive"])
    row.append(fps["false_negative"])
    return row


def generate_results_for_scenario(gt, res):
    scenario = { "stats": {}, "results": {} }
    scenario["stats"]["falls"] = gt["falls"]
    scenario["stats"]["fall_number"] = len(gt["falls"])

    for fps in res["cam1"].keys():
        scenario["results"][fps] = {
            "true_positive": 0,
            "false_positive": 0,
            "false_negative": 0
        }

    for fps in res["cam1"].keys():
        scenario["results"][fps]["falls"] = {}
        for cam in res.keys():
            scenario["results"][fps]["falls"][cam] = res[cam][fps]
    
    for fps in scenario["results"].keys():
        for cam in scenario["results"][fps]["falls"].keys():
            print(fps, cam)
            tp, fp, fn = get_stats(scenario["results"][fps]["falls"][cam], gt["falls"])
            scenario["results"][fps]["true_positive"] += tp
            scenario["results"][fps]["false_positive"] += fp
            scenario["results"][fps]["false_negative"] += fn

    return scenario

def get_stats(falls, gt):
    tp = 0
    fp = 0
    fn = 0

    START = 'fall_started_after'
    END = 'fall_ended_before'

    # Evaluate falls inside the ground truth interval
    for gt_fall in gt:
        in_the_interval = 0
        for fall in falls:
            if fall < gt_fall[END] and fall > gt_fall[START]:
                in_the_interval += 1
        if in_the_interval > 0:
            tp += 1
            #fp += in_the_interval - 1
    
    # Evaluate falls that are outside any given fall interval
    for fall in falls:
        for gt_fall in gt:
            if fall < gt_fall[END] and fall > gt_fall[START]:
                break
        else:
            fp += 1

    # Evaluate gt time intervals
    for gt_fall in gt:
        for fall in falls:
            if fall < gt_fall[END] and fall > gt_fall[START]:
                break
        else:
            fn += 1
    
    return (tp, fp, fn)

if __name__ == "__main__":
    labels = '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/tests/ground_truth/labels.json'
    results_dir = '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/tests/results'
    output_file = '/home/nagybalint/code/iot-home-security/src/raspberry_sec/module/falldetector/tests/summary.csv'
    generate_summary(results_dir, labels, output_file)