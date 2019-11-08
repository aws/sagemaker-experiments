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

from smexperiments import experiment, api_types


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


@pytest.fixture
def datetime_obj():
    return datetime.datetime(2017, 6, 16, 15, 55, 0)


def test_load(sagemaker_boto_client):
    sagemaker_boto_client.describe_experiment.return_value = {"Description": "description-value"}
    experiment_obj = experiment.Experiment.load(
        experiment_name="name-value", sagemaker_boto_client=sagemaker_boto_client
    )
    assert experiment_obj.experiment_name == "name-value"
    assert experiment_obj.description == "description-value"

    sagemaker_boto_client.describe_experiment.assert_called_with(ExperimentName="name-value")


def test_create(sagemaker_boto_client):
    sagemaker_boto_client.create_experiment.return_value = {"Arn": "arn:aws:1234"}
    experiment_obj = experiment.Experiment.create(
        experiment_name="name-value", sagemaker_boto_client=sagemaker_boto_client
    )
    assert experiment_obj.experiment_name == "name-value"
    sagemaker_boto_client.create_experiment.assert_called_with(ExperimentName="name-value")


def test_list(sagemaker_boto_client, datetime_obj):
    sagemaker_boto_client.list_experiments.return_value = {
        "ExperimentSummaries": [
            {
                "ExperimentName": "experiment-1",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
            {
                "ExperimentName": "experiment-2",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
        ]
    }
    expected = [
        api_types.ExperimentSummary(
            experiment_name="experiment-1",
            creation_time=datetime_obj,
            last_modified_time=datetime_obj,
        ),
        api_types.ExperimentSummary(
            experiment_name="experiment-2",
            creation_time=datetime_obj,
            last_modified_time=datetime_obj,
        ),
    ]
    assert expected == list(experiment.Experiment.list(sagemaker_boto_client=sagemaker_boto_client))


def test_list_trials_empty(sagemaker_boto_client):
    sagemaker_boto_client.list_trials.return_value = {"TrialSummaries": []}
    experiment_obj = experiment.Experiment(sagemaker_boto_client=sagemaker_boto_client)
    assert list(experiment_obj.list_trials()) == []


def test_list_trials_single(sagemaker_boto_client, datetime_obj):
    experiment_obj = experiment.Experiment(sagemaker_boto_client=sagemaker_boto_client)
    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {"Name": "trial-foo", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj}
        ]
    }

    assert list(experiment_obj.list_trials()) == [
        api_types.TrialSummary(
            name="trial-foo", creation_time=datetime_obj, last_modified_time=datetime_obj
        )
    ]


def test_list_trials_two_values(sagemaker_boto_client, datetime_obj):
    experiment_obj = experiment.Experiment(sagemaker_boto_client=sagemaker_boto_client)
    sagemaker_boto_client.list_trials.return_value = {
        "TrialSummaries": [
            {"Name": "trial-foo-1", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj},
            {"Name": "trial-foo-2", "CreationTime": datetime_obj, "LastModifiedTime": datetime_obj},
        ]
    }

    assert list(experiment_obj.list_trials()) == [
        api_types.TrialSummary(
            name="trial-foo-1", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
        api_types.TrialSummary(
            name="trial-foo-2", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
    ]


def test_next_token(sagemaker_boto_client, datetime_obj):
    experiment_obj = experiment.Experiment(sagemaker_boto_client)
    sagemaker_boto_client.list_trials.side_effect = [
        {
            "TrialSummaries": [
                {
                    "Name": "trial-foo-1",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
                {
                    "Name": "trial-foo-2",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
            ],
            "NextToken": "foo",
        },
        {
            "TrialSummaries": [
                {
                    "Name": "trial-foo-3",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                }
            ]
        },
    ]

    assert list(experiment_obj.list_trials()) == [
        api_types.TrialSummary(
            name="trial-foo-1", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
        api_types.TrialSummary(
            name="trial-foo-2", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
        api_types.TrialSummary(
            name="trial-foo-3", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
    ]

    sagemaker_boto_client.list_trials.assert_any_call(**{})
    sagemaker_boto_client.list_trials.assert_any_call(NextToken="foo")


def test_list_trials_call_args(sagemaker_boto_client):
    created_before = datetime.datetime(1999, 10, 12, 0, 0, 0)
    created_after = datetime.datetime(1990, 10, 12, 0, 0, 0)
    experiment_obj = experiment.Experiment(sagemaker_boto_client=sagemaker_boto_client)
    sagemaker_boto_client.list_trials.return_value = {}
    assert [] == list(
        experiment_obj.list_trials(created_after=created_after, created_before=created_before)
    )
    sagemaker_boto_client.list_trials.assert_called_with(
        CreatedBefore=created_before, CreatedAfter=created_after
    )


def test_experiment_create_trial_with_name(sagemaker_boto_client):
    experiment_obj = experiment.Experiment(sagemaker_boto_client=sagemaker_boto_client)
    experiment_obj.experiment_name = "someExperimentName"
    sagemaker_boto_client.create_trial.return_value = {
        "Arn": "arn:aws:1234",
        "TrialName": "someTrialName",
    }
    experiment_obj.create_trial(trial_name="someTrialName")
    sagemaker_boto_client.create_trial.assert_called_with(
        TrialName="someTrialName",
        ExperimentName="someExperimentName"
    )


def test_experiment_create_trial_with_prefix(sagemaker_boto_client):
    experiment_obj = experiment.Experiment(sagemaker_boto_client=sagemaker_boto_client)
    experiment_obj.experiment_name = 'someExperimentName'
    sagemaker_boto_client.create_trial.return_value = {
        "Arn": "arn:aws:1234",
        "TrialName": "someTrialName1234",
    }
    experiment_obj.create_trial(trial_name_prefix='someTrialName')
    _, _, kwargs = sagemaker_boto_client.mock_calls[0]
    assert kwargs['ExperimentName'] == 'someExperimentName'
    assert kwargs['TrialName'].startswith('someTrialName')


def test_save(sagemaker_boto_client):
    obj = experiment.Experiment(sagemaker_boto_client, experiment_name='foo', description='bar')
    sagemaker_boto_client.update_experiment.return_value = {}
    obj.save()
    sagemaker_boto_client.update_experiment.assert_called_with(ExperimentName='foo', Description='bar')


def test_delete(sagemaker_boto_client):
    obj = experiment.Experiment(sagemaker_boto_client, experiment_name='foo', description='bar')
    sagemaker_boto_client.delete_experiment.return_value = {}
    obj.delete()
    sagemaker_boto_client.delete_experiment.assert_called_with(ExperimentName='foo')
