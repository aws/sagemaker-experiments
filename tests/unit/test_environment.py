# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#       http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import json
import os
import shutil
import tempfile
import unittest

# https://github.com/coala/coala-bears/issues/2862
from unittest.mock import patch

import pytest

from smexperiments import _environment


@pytest.fixture
def tempdir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


@pytest.fixture
def training_job_env():
    old_value = os.environ.get("TRAINING_JOB_ARN")
    os.environ["TRAINING_JOB_ARN"] = "arn:1234aBcDe"
    yield os.environ
    del os.environ["TRAINING_JOB_ARN"]
    if old_value:
        os.environ["TRAINING_JOB_ARN"] = old_value


def test_processing_job_environment(tempdir):
    config_path = os.path.join(tempdir, "config.json")
    with open(config_path, "w") as f:
        f.write(json.dumps({"ProcessingJobArn": "arn:1234aBcDe"}))
    environment = _environment.TrialComponentEnvironment.load(processing_job_config_path=config_path)

    assert _environment.EnvironmentType.SageMakerProcessingJob == environment.environment_type
    assert "arn:1234aBcDe" == environment.source_arn


def test_training_job_environment(training_job_env):
    environment = _environment.TrialComponentEnvironment.load()
    assert _environment.EnvironmentType.SageMakerTrainingJob == environment.environment_type
    assert "arn:1234aBcDe" == environment.source_arn


def test_no_environment():
    assert _environment.TrialComponentEnvironment.load() is None


def test_resolve_trial_component(training_job_env, sagemaker_boto_client):
    trial_component_name = "foo-bar"
    sagemaker_boto_client.list_trial_components.return_value = {
        "TrialComponentSummaries": [{"TrialComponentName": trial_component_name}]
    }
    sagemaker_boto_client.describe_trial_component.return_value = {"TrialComponentName": trial_component_name}
    environment = _environment.TrialComponentEnvironment.load()

    tc = environment.get_trial_component(sagemaker_boto_client)

    assert trial_component_name == tc.trial_component_name
    sagemaker_boto_client.list_trial_components.assert_called_with(SourceArn="arn:1234aBcDe")
    sagemaker_boto_client.describe_trial_component.assert_called_with(TrialComponentName=trial_component_name)


@unittest.mock.patch("time.sleep")
@unittest.mock.patch("time.time")
def test_resolve_trial_component_fails(mock_time, mock_sleep, sagemaker_boto_client, training_job_env):
    mock_time.side_effect = [100, 500]
    environment = _environment.TrialComponentEnvironment.load()
    assert environment.get_trial_component(sagemaker_boto_client) is None
