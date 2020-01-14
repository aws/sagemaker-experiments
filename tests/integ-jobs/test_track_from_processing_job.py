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
import pytest
from tests.helpers import *

from smexperiments import trial_component, api_types


def wait_for_job(job, sagemaker_client):
    with timeout(minutes=15):
        while True:
            response = sagemaker_client.describe_processing_job(ProcessingJobName=job)
            status = response['ProcessingJobStatus']
            print(f'Processing job status: {status}')
            if status == 'Failed':
                print(response)
                dump_logs(job)
                pytest.fail('Processing job failed: ' + job)
            if status == 'Completed':
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(30)

@pytest.mark.skip(reason="to be only run manually, integ/canaries already cover this scenario")
def test_track_from_processing_job(sagemaker_boto_client, processing_job_name):
    processing_job = sagemaker_boto_client.describe_processing_job(ProcessingJobName=processing_job_name)

    source_arn = processing_job['ProcessingJobArn']
    wait_for_job(processing_job_name, sagemaker_boto_client)
    trial_component_name = sagemaker_boto_client.list_trial_components(
        SourceArn=source_arn)['TrialComponentSummaries'][0]['TrialComponentName']

    trial_component_obj = trial_component.TrialComponent.load(
        trial_component_name=trial_component_name)
    assert {
        'p1': 1.0,
        'SageMaker.InstanceType': 'ml.m5.large',
        'SageMaker.InstanceCount': 1.0,
        'SageMaker.VolumeSizeInGB': 10.0
    } == trial_component_obj.parameters

    image_uri = processing_job['AppSpecification']['ImageUri']
    assert {
        'SageMaker.ImageUri': api_types.TrialComponentArtifact(value=image_uri)
    } == trial_component_obj.input_artifacts

    assert not trial_component_obj.output_artifacts
    assert not trial_component_obj.metrics
    assert source_arn == trial_component_obj.source.source_arn
    assert 'Completed' == trial_component_obj.status.primary_status
