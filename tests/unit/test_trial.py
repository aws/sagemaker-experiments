# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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


def test_create_with_tags(sagemaker_boto_client):
    sagemaker_boto_client.create_trial.return_value = {
        "Arn": "arn:aws:1234",
        "TrialName": "name-value",
    }
    tags = [{"Key": "foo", "Value": "bar"}]
    trial_obj = trial.Trial.create(
        trial_name="name-value",
        experiment_name="experiment-name-value",
        sagemaker_boto_client=sagemaker_boto_client,
        tags=tags,
    )
    assert trial_obj.trial_name == "name-value"
    sagemaker_boto_client.create_trial.assert_called_with(
        TrialName="name-value", ExperimentName="experiment-name-value", Tags=[{"Key": "foo", "Value": "bar"}]
    )


def test_create_no_name(sagemaker_boto_client):
    sagemaker_boto_client.create_trial.return_value = {}
    trial.Trial.create(experiment_name="experiment-name-value", sagemaker_boto_client=sagemaker_boto_client)
    _, _, kwargs = sagemaker_boto_client.mock_calls[0]
    assert kwargs["TrialName"]  # confirm that a TrialName was passed


def test_create_with_trial_components(sagemaker_boto_client):
    sagemaker_boto_client.create_trial.return_value = {
        "Arn": "arn:aws:1234",
        "TrialName": "name-value",
    }
    tc = trial_component.TrialComponent(trial_component_name="tc-foo", sagemaker_boto_client=sagemaker_boto_client)

    trial_obj = trial.Trial.create(
        trial_name="name-value",
        experiment_name="experiment-name-value",
        trial_components=[tc],
        sagemaker_boto_client=sagemaker_boto_client,
    )
    assert trial_obj.trial_name == "name-value"
    sagemaker_boto_client.create_trial.assert_called_with(
        TrialName="name-value", ExperimentName="experiment-name-value"
    )
    sagemaker_boto_client.associate_trial_component.assert_called_with(
        TrialName="name-value", TrialComponentName=tc.trial_component_name
    )


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
    tc_tracker = tracker.Tracker(tc2, unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock())
    t.add_trial_component(tc_tracker)
    sagemaker_boto_client.associate_trial_component.assert_called_with(
        TrialName="bar", TrialComponentName=tc2.trial_component_name
    )


def test_add_trial_component_from_trial_component_summary(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    tcs = api_types.TrialComponentSummary()
    tcs.trial_component_name = "tcs-foo"
    t.add_trial_component(tcs)
    sagemaker_boto_client.associate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="tcs-foo")


def test_remove_trial_component(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    t.remove_trial_component("foo")
    sagemaker_boto_client.disassociate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="foo")


def test_remove_trial_component_from_trial_component_summary(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    tcs = api_types.TrialComponentSummary()
    tcs.trial_component_name = "tcs-foo"
    t.remove_trial_component(tcs)
    sagemaker_boto_client.disassociate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="tcs-foo")


def test_remove_trial_component_from_tracker(sagemaker_boto_client):
    t = trial.Trial(sagemaker_boto_client)
    t.trial_name = "bar"
    tc = trial_component.TrialComponent(trial_component_name="tc-foo", sagemaker_boto_client=sagemaker_boto_client)
    trkr = tracker.Tracker(tc, unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock())
    t.remove_trial_component(trkr)
    sagemaker_boto_client.disassociate_trial_component.assert_called_with(TrialName="bar", TrialComponentName="tc-foo")


def test_list_trials_without_experiment_name(sagemaker_boto_client, datetime_obj):
    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {
                "TrialName": "trial-1",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
            {
                "TrialName": "trial-2",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
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
            {
                "TrialName": "trial-1",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
            {
                "TrialName": "trial-2",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
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
            {
                "TrialName": "trial-1",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
            {
                "TrialName": "trial-2",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
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


def test_search(sagemaker_boto_client):
    sagemaker_boto_client.search.return_value = {
        "Results": [
            {
                "Trial": {
                    "TrialName": "trial-1",
                    "TrialArn": "arn::trial-1",
                    "DisplayName": "Trial1",
                }
            },
            {
                "Trial": {
                    "TrialName": "trial-2",
                    "TrialArn": "arn::trial-2",
                    "DisplayName": "Trial2",
                }
            },
        ]
    }
    expected = [
        api_types.TrialSearchResult(trial_name="trial-1", trial_arn="arn::trial-1", display_name="Trial1"),
        api_types.TrialSearchResult(trial_name="trial-2", trial_arn="arn::trial-2", display_name="Trial2"),
    ]
    assert expected == list(trial.Trial.search(sagemaker_boto_client=sagemaker_boto_client))


def test_boto_ignore():
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")
    assert obj._boto_ignore() == ["ResponseMetadata", "CreatedBy"]


def test_delete(sagemaker_boto_client):
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")
    sagemaker_boto_client.delete_trial.return_value = {}
    obj.delete()
    sagemaker_boto_client.delete_trial.assert_called_with(TrialName="foo")


def test_delete_all_with_incorrect_action_name(sagemaker_boto_client):
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")
    with pytest.raises(ValueError):
        obj.delete_all(action="abc")


def test_delete_all(sagemaker_boto_client):
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")

    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {"TrialName": "trial-1", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj},
            {"TrialName": "trial-2", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj},
        ]
    }

    sagemaker_boto_client.list_trial_components.side_effect = [
        {
            "TrialComponentSummaries": [
                {
                    "TrialComponentName": "trial-component-1",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
                {
                    "TrialComponentName": "trial-component-2",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
                {
                    "TrialComponentName": "trial-component-3",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
                {
                    "TrialComponentName": "trial-component-4",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
            ]
        },
    ]

    sagemaker_boto_client.describe_trial_component.side_effect = [
        {"TrialComponentName": "trial-component-1"},
        {"TrialComponentName": "trial-component-2"},
        {"TrialComponentName": "trial-component-3"},
        {"TrialComponentName": "trial-component-4"},
    ]

    sagemaker_boto_client.delete_trial_component.return_value = {}
    sagemaker_boto_client.delete_trial.return_value = {}

    obj.delete_all(action="--force")

    sagemaker_boto_client.delete_trial.assert_called_with(TrialName="foo")

    delete_trial_component_expected_calls = [
        unittest.mock.call(TrialComponentName="trial-component-1"),
        unittest.mock.call(TrialComponentName="trial-component-2"),
        unittest.mock.call(TrialComponentName="trial-component-3"),
        unittest.mock.call(TrialComponentName="trial-component-4"),
    ]
    assert delete_trial_component_expected_calls == sagemaker_boto_client.delete_trial_component.mock_calls


def test_delete_all_fail(sagemaker_boto_client):
    obj = trial.Trial(sagemaker_boto_client, trial_name="foo")
    sagemaker_boto_client.list_trials.side_effect = Exception
    with pytest.raises(Exception) as e:
        obj.delete_all(action="--force")
    assert str(e.value) == "Failed to delete, please try again."
