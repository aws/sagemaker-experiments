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
import pytest
import unittest.mock

from smexperiments import training_job, api_types


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


def test_search(sagemaker_boto_client):
    sagemaker_boto_client.search.return_value = {
        "Results": [
            {
                "TrainingJob": {
                    "TrainingJobName": "training-1",
                    "TrainingJobArn": "arn::training-1",
                    "HyperParameters": {"learning_rate": "0.1"},
                }
            },
            {
                "TrainingJob": {
                    "TrainingJobName": "training-2",
                    "TrainingJobArn": "arn::training-2",
                    "HyperParameters": {"learning_rate": "0.2"},
                }
            },
        ]
    }
    expected = [
        api_types.TrainingJobSearchResult(
            training_job_name="training-1",
            training_job_arn="arn::training-1",
            hyper_parameters={"learning_rate": "0.1"},
        ),
        api_types.TrainingJobSearchResult(
            training_job_name="training-2",
            training_job_arn="arn::training-2",
            hyper_parameters={"learning_rate": "0.2"},
        ),
    ]
    assert expected == list(training_job.TrainingJob.search(sagemaker_boto_client=sagemaker_boto_client))
