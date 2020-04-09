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


@pytest.mark.slow
def test_track_from_processing_job(sagemaker_boto_client, processing_job_name):
    processing_job_name = "smexperiments-integ-549de818-b4bd-42d0-8ce7-1cb4cb3573d9"
    get_job = lambda: sagemaker_boto_client.describe_processing_job(ProcessingJobName=processing_job_name)
    processing_job = get_job()

    source_arn = processing_job["ProcessingJobArn"]
    wait_for_job(processing_job_name, get_job, "ProcessingJobStatus")

    print(processing_job)
    if "ProcessingStartTime" in processing_job:
        start = to_seconds(processing_job["ProcessingStartTime"])
        end = to_seconds(processing_job["ProcessingEndTime"])
        print("Processing job took: {} seconds".format(end - start))

    trial_component_name = sagemaker_boto_client.list_trial_components(SourceArn=source_arn)["TrialComponentSummaries"][
        0
    ]["TrialComponentName"]

    trial_component_obj = trial_component.TrialComponent.load(trial_component_name=trial_component_name)
    assert {
        "SageMaker.InstanceType": "ml.m5.large",
        "SageMaker.InstanceCount": 1.0,
        "SageMaker.VolumeSizeInGB": 10.0,
    } == trial_component_obj.parameters

    image_uri = processing_job["AppSpecification"]["ImageUri"]
    assert {
        "SageMaker.ImageUri": api_types.TrialComponentArtifact(value=image_uri)
    } == trial_component_obj.input_artifacts

    assert not trial_component_obj.output_artifacts, "should be no output artifacts"
    assert not trial_component_obj.metrics, "should be no metrics"
    assert source_arn == trial_component_obj.source.source_arn, "source ARNs should match"
    assert trial_component_obj.status.primary_status in ["Completed", "Failed"], "Status should be Completed or Failed"
