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

from smexperiments.training_job import TrainingJob
from smexperiments.search_expression import SearchExpression, Filter, Operator
from tests.helpers import retry


@pytest.mark.slow
def test_search(sagemaker_boto_client, training_job_name, docker_image):
    def validate():
        training_job_searched = []
        search_filter = Filter(name="TrainingJobName", operator=Operator.EQUALS, value=training_job_name)
        search_expression = SearchExpression(filters=[search_filter])
        for s in TrainingJob.search(
            search_expression=search_expression,
            max_results=10,
            sagemaker_boto_client=sagemaker_boto_client,
        ):
            training_job_searched.append(s)

        assert len(training_job_searched) == 1
        assert training_job_searched[0].training_job_name == training_job_name
        assert training_job_searched[0].input_data_config[0]["ChannelName"] == "train"
        assert training_job_searched[0].algorithm_specification == {
            "TrainingImage": docker_image,
            "TrainingInputMode": "File",
        }
        assert training_job_searched[0].resource_config == {
            "InstanceType": "ml.m5.large",
            "InstanceCount": 1,
            "VolumeSizeInGB": 10,
        }
        assert training_job_searched[0].stopping_condition == {"MaxRuntimeInSeconds": 900}
        assert training_job_searched  # sanity test

    retry(validate)
