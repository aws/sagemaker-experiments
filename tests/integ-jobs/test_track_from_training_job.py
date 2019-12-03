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

import sys

import boto3

from tests.helpers import *
from smexperiments import trial_component


def dump_logs(job):
    logs = boto3.client('logs')
    [log_stream] = logs.describe_log_streams(logGroupName="/aws/sagemaker/TrainingJobs",
                                             logStreamNamePrefix=job)['logStreams']
    log_stream_name = log_stream['logStreamName']
    next_token = None
    while True:
        if next_token:
            log_event_response = logs.get_log_events(
                logGroupName="/aws/sagemaker/TrainingJobs",
                logStreamName=log_stream_name,
                nextToken=next_token)
        else:
            log_event_response = logs.get_log_events(
                logGroupName="/aws/sagemaker/TrainingJobs",
                logStreamName=log_stream_name)
        next_token = log_event_response['nextForwardToken']
        events = log_event_response['events']
        if not events:
            break
        for event in events:
            print(event['message'])


def wait_for_job(job, sagemaker_client):
    with timeout(minutes=15):
        while True:
            response = sagemaker_client.describe_training_job(TrainingJobName=job)
            status = response['TrainingJobStatus']
            if status == 'Failed':
                print(response)
                dump_logs(job)
                pytest.fail('Training job failed: ' + job)
            if status == 'Completed':
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(30)


def test_track_from_training_job(sagemaker_boto_client, training_job_name):
    tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)
    source_arn = tj['TrainingJobArn']
    wait_for_job(training_job_name, sagemaker_boto_client)
    tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)

    trial_component_name = list(trial_component.TrialComponent.list(
        source_arn=source_arn, sagemaker_boto_client=sagemaker_boto_client))[0].trial_component_name

    def validate():
        tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)
        trial_component_obj = trial_component.TrialComponent.load(trial_component_name=trial_component_name,
                                                                  sagemaker_boto_client=sagemaker_boto_client)

        assert source_arn == trial_component_obj.source.source_arn
        assert to_seconds(tj['TrainingStartTime']) == to_seconds(trial_component_obj.start_time)
        assert to_seconds(tj['TrainingEndTime']) == to_seconds(trial_component_obj.end_time)
        metrics = trial_component_obj.metrics
        for metric_summary in metrics:
            assert metric_summary.count == 2
            assert metric_summary.min == 0.0
            assert metric_summary.max == 1.0
        assert 4 == len(metrics)

        assert trial_component_obj.status.primary_status == 'Completed'

    try:
        retry(lambda: dump_logs(training_job_name))
    except:
        pass  # best effort attempt to print logs, there may be no logs if script didn't print anything
    retry(validate)


def to_seconds(dt):
    return int(dt.timestamp())
