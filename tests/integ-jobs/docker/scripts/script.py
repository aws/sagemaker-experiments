import datetime
import time

from smexperiments import tracker

import os

for key, value in os.environ.items():
    print(key, value)

with tracker.Tracker.load() as tracker:
    tracker.log_parameter('p1', 1.0)
    if 'TRAINING_JOB_ARN' in os.environ:
        for i in range(2):
            tracker.log_metric('A', i)
        for i in range(2):
            tracker.log_metric('B', i)
        for i in range(2):
            tracker.log_metric('C', i)
        for i in range(2):
            time.sleep(0.003)
            tracker.log_metric('D', i)
        time.sleep(15)
