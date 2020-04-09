# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import sys
import boto3
import pytest

from tests.helpers import *
from smexperiments import trial_component


@pytest.mark.slow
def test_track_from_training_job(sagemaker_boto_client, training_job_name):
    training_job_name = "smexperiments-integ-eca5c064-3a64-433e-a30a-2963338d71d8"
    get_job = lambda: sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)
    tj = get_job()
    source_arn = tj["TrainingJobArn"]
    wait_for_job(training_job_name, get_job, "TrainingJobStatus")
    tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)
    start = to_seconds(tj["TrainingStartTime"])
    end = to_seconds(tj["TrainingEndTime"])
    print("Training job took: {} seconds".format(end - start))

    trial_component_name = list(
        trial_component.TrialComponent.list(source_arn=source_arn, sagemaker_boto_client=sagemaker_boto_client)
    )[0].trial_component_name

    def validate():
        tj = get_job()
        trial_component_obj = trial_component.TrialComponent.load(
            trial_component_name=trial_component_name, sagemaker_boto_client=sagemaker_boto_client
        )

        assert source_arn == trial_component_obj.source.source_arn
        assert start == to_seconds(trial_component_obj.start_time)
        assert end == to_seconds(trial_component_obj.end_time)
        metrics = trial_component_obj.metrics
        for metric_summary in metrics:
            assert metric_summary.count == 2
            assert metric_summary.min == 0.0
            assert metric_summary.max == 1.0
        assert 0 == len(metrics), "Job is failing, expected no metrics"

        assert trial_component_obj.status.primary_status in ["Completed", "Failed"]

    # for debugging
    # try:
    #    retry(lambda: dump_logs(training_job_name, "TrainingJobs"))
    # except:
    #    pass  # best effort attempt to print logs, there may be no logs if script didn't print anything
    retry(validate)
