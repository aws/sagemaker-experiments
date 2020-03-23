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

import datetime

from smexperiments import trial, api_types, trial_component, tracker


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


@pytest.fixture
def datetime_obj():
    return datetime.datetime(2017, 6, 16, 15, 55, 0)


def test_load(sagemaker_boto_client):
    sagemaker_boto_client.describe_trial.return_value = {"ExperimentName": "experiment-name-value"}
    trial_obj = trial.Trial.load(trial_name="name-value", sagemaker_boto_client=sagemaker_boto_client)
    assert trial_obj.trial_name == "name-value"
    assert trial_obj.experiment_name == "experiment-name-value"
    sagemaker_boto_client.describe_trial.assert_called_with(TrialName="name-value")


def test_create(sagemaker_boto_client):
    sagemaker_boto_client.create_trial.return_value = {
        "Arn": "arn:aws:1234",
        "TrialName": "name-value",
    }
    trial_obj = trial.Trial.create(
        trial_name="name-value", experiment_name="experiment-name-value", sagemaker_boto_client=sagemaker_boto_client
    )
    assert trial_obj.trial_name == "name-value"
    sagemaker_boto_client.create_trial.assert_called_with(
        TrialName="name-value", ExperimentName="experiment-name-value"
    )


def test_create_no_name(sagemaker_boto_client):
    sagemaker_boto_client.create_trial.return_value = {}
    trial.Trial.create(experiment_name="experiment-name-value", sagemaker_boto_client=sagemaker_boto_client)
    _, _, kwargs = sagemaker_boto_client.mock_calls[0]
    assert kwargs["TrialName"]  # confirm that a TrialName was passed


def test_add_trial_component(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    t.add_trial_component("foo")
    sagemaker_boto_client.associate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="foo")

    tc = trial_component.TrialComponent(trial_component_name="tc-foo", sagemaker_boto_client=sagemaker_boto_client)
    t.add_trial_component(tc)
    sagemaker_boto_client.associate_trial_component.assert_called_with(
        TrialName="bar", TrialComponentName=tc.trial_component_name
    )

    tc2 = trial_component.TrialComponent(trial_component_name="tc-foo2", sagemaker_boto_client=sagemaker_boto_client)
    tc_tracker = tracker.Tracker(tc2, unittest.mock.Mock(), unittest.mock.Mock())
    t.add_trial_component(tc_tracker)
    sagemaker_boto_client.associate_trial_component.assert_called_with(
        TrialName="bar", TrialComponentName=tc2.trial_component_name
    )


def test_remove_trial_component(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    t.remove_trial_component("foo")
    sagemaker_boto_client.disassociate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="foo")


def test_remove_trial_component_from_tracker(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    tc = trial_component.TrialComponent(trial_component_name="tc-foo", sagemaker_boto_client=sagemaker_boto_client)
    trkr = tracker.Tracker(tc, unittest.mock.Mock(), unittest.mock.Mock())
    t.remove_trial_component(trkr)
    sagemaker_boto_client.disassociate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="tc-foo")


def test_list_trials_without_experiment_name(sagemaker_boto_client, datetime_obj):
    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {"TrialName": "trial-1", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj,},
            {"TrialName": "trial-2", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj,},
        ]
    }
    expected = [
        api_types.TrialSummary(trial_name="trial-1", creation_time=datetime_obj, last_modified_time=datetime_obj),
        api_types.TrialSummary(trial_name="trial-2", creation_time=datetime_obj, last_modified_time=datetime_obj),
    ]
    assert expected == list(trial.Trial.list(sagemaker_boto_client=sagemaker_boto_client))
    sagemaker_boto_client.list_trials.assert_called_with(**{})


def test_list_trials_with_experiment_name(sagemaker_boto_client, datetime_obj):
    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {"TrialName": "trial-1", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj,},
            {"TrialName": "trial-2", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj,},
        ]
    }
    expected = [
        api_types.TrialSummary(trial_name="trial-1", creation_time=datetime_obj, last_modified_time=datetime_obj),
        api_types.TrialSummary(trial_name="trial-2", creation_time=datetime_obj, last_modified_time=datetime_obj),
    ]
    assert expected == list(trial.Trial.list(experiment_name="foo", sagemaker_boto_client=sagemaker_boto_client))
    sagemaker_boto_client.list_trials.assert_called_with(ExperimentName="foo")


def test_list_trials_with_trial_component_name(sagemaker_boto_client, datetime_obj):
    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {"TrialName": "trial-1", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj,},
            {"TrialName": "trial-2", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj,},
        ]
    }
    expected = [
        api_types.TrialSummary(trial_name="trial-1", creation_time=datetime_obj, last_modified_time=datetime_obj),
        api_types.TrialSummary(trial_name="trial-2", creation_time=datetime_obj, last_modified_time=datetime_obj),
    ]
    assert expected == list(
        trial.Trial.list(trial_component_name="tc-foo", sagemaker_boto_client=sagemaker_boto_client)
    )
    sagemaker_boto_client.list_trials.assert_called_with(TrialComponentName="tc-foo")


def test_delete(sagemaker_boto_client):
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")
    sagemaker_boto_client.delete_trial.return_value = {}
    obj.delete()
    sagemaker_boto_client.delete_trial.assert_called_with(TrialName="foo")


def test_boto_ignore():
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")
    assert obj._boto_ignore() == ["ResponseMetadata", "CreatedBy"]
