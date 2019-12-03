# Copyright 019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

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
