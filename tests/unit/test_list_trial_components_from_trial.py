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

from smexperiments import trial, api_types


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


@pytest.fixture
def datetime_obj():
    return datetime.datetime(2017, 6, 16, 15, 55, 0)


def test_list_trial_components(sagemaker_boto_client, datetime_obj):
    sagemaker_boto_client.list_trial_components.return_value = {
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
        ]
    }
    expected = [
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-1",
            creation_time=datetime_obj,
            last_modified_time=datetime_obj,
        ),
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-2",
            creation_time=datetime_obj,
            last_modified_time=datetime_obj,
        ),
    ]

    trial_obj = trial.Trial(sagemaker_boto_client=sagemaker_boto_client)

    assert expected == list(trial_obj.list_trial_components())


def test_list_trial_components_empty(sagemaker_boto_client):
    sagemaker_boto_client.list_trial_components.return_value = {"TrialComponentSummaries": []}
    trial_obj = trial.Trial(sagemaker_boto_client=sagemaker_boto_client)
    assert list(trial_obj.list_trial_components()) == []


def test_list_trial_components_single(sagemaker_boto_client, datetime_obj):
    trial_obj = trial.Trial(sagemaker_boto_client=sagemaker_boto_client)
    sagemaker_boto_client.list_trial_components.return_value = {
        "TrialComponentSummaries": [
            {
                "TrialComponentName": "trial-component-foo",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            }
        ]
    }

    assert list(trial_obj.list_trial_components()) == [
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-foo", creation_time=datetime_obj, last_modified_time=datetime_obj
        )
    ]


def test_list_trial_components_two_values(sagemaker_boto_client, datetime_obj):
    trial_obj = trial.Trial(sagemaker_boto_client=sagemaker_boto_client)
    sagemaker_boto_client.list_trial_components.return_value = {
        "TrialComponentSummaries": [
            {
                "TrialComponentName": "trial-component-foo-1",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
            {
                "TrialComponentName": "trial-component-foo-2",
                "CreationTime": datetime_obj,
                "LastModifiedTime": datetime_obj,
            },
        ]
    }

    assert list(trial_obj.list_trial_components()) == [
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-foo-1", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-foo-2", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
    ]


def test_next_token(sagemaker_boto_client, datetime_obj):
    trial_obj = trial.Trial(sagemaker_boto_client)
    sagemaker_boto_client.list_trial_components.side_effect = [
        {
            "TrialComponentSummaries": [
                {
                    "TrialComponentName": "trial-component-foo-1",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
                {
                    "TrialComponentName": "trial-component-foo-2",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                },
            ],
            "NextToken": "foo",
        },
        {
            "TrialComponentSummaries": [
                {
                    "TrialComponentName": "trial-component-foo-3",
                    "CreationTime": datetime_obj,
                    "LastModifiedTime": datetime_obj,
                }
            ]
        },
    ]

    assert list(trial_obj.list_trial_components()) == [
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-foo-1", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-foo-2", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
        api_types.TrialComponentSummary(
            trial_component_name="trial-component-foo-3", creation_time=datetime_obj, last_modified_time=datetime_obj
        ),
    ]

    sagemaker_boto_client.list_trial_components.assert_any_call(**{})
    sagemaker_boto_client.list_trial_components.assert_any_call(NextToken="foo")


def test_list_trial_components_call_args(sagemaker_boto_client):
    created_before = datetime.datetime(1999, 10, 12, 0, 0, 0)
    created_after = datetime.datetime(1990, 10, 12, 0, 0, 0)
    trial_name = "foo-trial"
    next_token = "thetoken"
    max_results = 99

    trial_obj = trial.Trial(sagemaker_boto_client=sagemaker_boto_client)
    trial_obj.trial_name = trial_name

    sagemaker_boto_client.list_trial_components.return_value = {}
    assert [] == list(
        trial_obj.list_trial_components(
            created_after=created_after, created_before=created_before, next_token=next_token, max_results=max_results
        )
    )
    sagemaker_boto_client.list_trial_components.assert_called_with(
        CreatedBefore=created_before,
        CreatedAfter=created_after,
        TrialName=trial_name,
        NextToken=next_token,
        MaxResults=max_results,
    )
