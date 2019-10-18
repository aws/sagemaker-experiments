# Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from __future__ import absolute_import

import os
import pytest
import mock
import uuid

from sagemaker.experiments.tracker import Tracker


@pytest.fixture
def mock_boto_client():
    return mock.Mock()


@mock.patch("boto3.client")
def test_tracker_gets_default_boto_client_if_none_supplied(boto_client):
    tracker = Tracker(display_name="PreProcessing")
    boto_client.assert_called_once_with("sagemaker")
    assert tracker.sagemaker_boto_client


def test_create_tracker_in_training_job(mock_boto_client):
    training_job_arn = "arn:aws:sagemaker:test:1234:training-job/abcd"

    mock_boto_client.list_trial_components.return_value = {
        "TrialComponents": [
            {
                "TrialComponentName": "abcd",
                "TrialComponentArn": "arn:aws:sagemaker:test:1234:experiment-trial-component/abcd",
            }
        ]
    }

    with mock.patch.dict(os.environ, {"TRAINING_JOB_ARN": training_job_arn}):
        tracker = Tracker(sagemaker_boto_client=mock_boto_client)

    assert tracker.source_arn == training_job_arn
    assert tracker.component_name == "abcd"
    assert not tracker.failed_mode
    mock_boto_client.create_trial_component.assert_not_called()


def test_create_tracker_in_training_job_failed_mode(mock_boto_client):
    training_job_arn = "arn:aws:sagemaker:test:1234:training-job/abcd"

    mock_boto_client.list_trial_components.side_effect = RuntimeError()

    with mock.patch.dict(os.environ, {"TRAINING_JOB_ARN": training_job_arn}):
        tracker = Tracker(sagemaker_boto_client=mock_boto_client)

    assert tracker.source_arn == training_job_arn
    assert tracker.failed_mode
    mock_boto_client.create_trial_component.assert_not_called()


@mock.patch.object(uuid, "uuid4")
def test_create_tracker_in_notebook(mock_uuid, mock_boto_client):
    mock_uuid.return_value = "uuid"
    tracker = Tracker(display_name="Training", sagemaker_boto_client=mock_boto_client)
    assert tracker.component_name == "Training-uuid"
    assert not tracker.failed_mode
    mock_boto_client.create_trial_component.assert_called_once_with(
        TrialComponentName=tracker.component_name, DisplayName="Training"
    )


@mock.patch.object(uuid, "uuid4")
def test_create_tracker_in_notebook_no_source_arn(mock_uuid, mock_boto_client):
    mock_uuid.return_value = "uuid"
    tracker = Tracker(display_name="PreProcessing", sagemaker_boto_client=mock_boto_client)

    assert not tracker.source_arn
    assert tracker.component_name == "PreProcessing-uuid"
    assert not tracker.failed_mode
    mock_boto_client.create_trial_component.assert_called_once_with(
        TrialComponentName=tracker.component_name, DisplayName="PreProcessing"
    )


def test_create_tracker_in_notebook_no_display_name(mock_boto_client):
    with pytest.raises(ValueError):
        Tracker(sagemaker_boto_client=mock_boto_client)
