import datetime
import time

from smexperiments import tracker

import os

for key, value in os.environ.items():
    print(key, value)
with tracker.Tracker.load() as tracker:
    tracker.log_parameter('p1', 1.0)
    for i in range(2):
        tracker.log_metric('test-metric-tracker', i)
    for i in range(2):
        tracker.log_metric('test-metric-writer-default-timestamp', i)
    for i in range(2):
        tracker.log_metric('test-metric-writer-timestamp', i, timestamp=datetime.datetime.now())
    for i in range(2):
        time.sleep(0.003)
        tracker.log_metric('test-metric-writer-different-timestamps', i, timestamp=datetime.datetime.now())
