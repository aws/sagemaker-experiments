from smexperiments import tracker

with tracker.Tracker.load() as tracker:
    tracker.log_parameter('p1', 1.0)
    tracker.log_metric('test-metric', 1.0)
