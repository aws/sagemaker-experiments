import datetime
import time

from smexperiments import tracker

import os

for key, value in os.environ.items():
    print(key, value)

with tracker.Tracker.load() as tracker:
    for key, value in vars(tracker.trial_component.sagemaker_boto_client).items():
        print (key, value)

    tracker.log_parameter('p1', 1.0)
    for i in range(2):
        tracker.log_metric('A', i)
    for i in range(2):
        tracker.log_metric('B', i)
    for i in range(2):
        tracker.log_metric('C', i, timestamp=datetime.datetime.now())
    for i in range(2):
        time.sleep(0.003)
        tracker.log_metric('D', i, timestamp=datetime.datetime.now())

time.sleep(15)
