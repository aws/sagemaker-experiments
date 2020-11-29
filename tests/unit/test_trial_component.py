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
from smexperiments import trial_component, api_types

import datetime
import pytest
import unittest.mock


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


def test_create(sagemaker_boto_client):
    sagemaker_boto_client.create_trial_component.return_value = {
        "TrialComponentArn": "bazz",
    }
    obj = trial_component.TrialComponent.create(
        trial_component_name="foo", display_name="bar", sagemaker_boto_client=sagemaker_boto_client
    )
    sagemaker_boto_client.create_trial_component.assert_called_with(TrialComponentName="foo", DisplayName="bar")
    assert "foo" == obj.trial_component_name
    assert "bar" == obj.display_name
    assert "bazz" == obj.trial_component_arn


def test_create_with_tags(sagemaker_boto_client):
    sagemaker_boto_client.create_trial_component.return_value = {
        "TrialComponentArn": "bazz",
    }
    tags = [{"Key": "foo", "Value": "bar"}]
    obj = trial_component.TrialComponent.create(
        trial_component_name="foo", display_name="bar", sagemaker_boto_client=sagemaker_boto_client, tags=tags
    )
    sagemaker_boto_client.create_trial_component.assert_called_with(
        TrialComponentName="foo", DisplayName="bar", Tags=[{"Key": "foo", "Value": "bar"}]
    )


def test_load(sagemaker_boto_client):
    now = datetime.datetime.now(datetime.timezone.utc)

    sagemaker_boto_client.describe_trial_component.return_value = {
        "TrialComponentArn": "A",
        "TrialComponentName": "B",
        "DisplayName": "C",
        "Status": {"PrimaryStatus": "InProgress", "Message": "D"},
        "Parameters": {"E": {"NumberValue": 1.0}, "F": {"StringValue": "G"}},
        "InputArtifacts": {"H": {"Value": "s3://foo/bar", "MediaType": "text/plain"}},
        "OutputArtifacts": {"I": {"Value": "s3://whizz/bang", "MediaType": "text/plain"}},
        "Metrics": [
            {
                "MetricName": "J",
                "Count": 1,
                "Min": 1.0,
                "Max": 2.0,
                "Avg": 3.0,
                "StdDev": 4.0,
                "SourceArn": "K",
                "Timestamp": now,
            }
        ],
    }
    obj = trial_component.TrialComponent.load(trial_component_name="foo", sagemaker_boto_client=sagemaker_boto_client)
    sagemaker_boto_client.describe_trial_component.assert_called_with(TrialComponentName="foo")
    assert "A" == obj.trial_component_arn
    assert "B" == obj.trial_component_name
    assert "C" == obj.display_name
    assert api_types.TrialComponentStatus(primary_status="InProgress", message="D") == obj.status
    assert {"E": 1.0, "F": "G"} == obj.parameters
    assert {"H": api_types.TrialComponentArtifact(value="s3://foo/bar", media_type="text/plain")}
    assert {"I": api_types.TrialComponentArtifact(value="s3://whizz/bang", media_type="text/plain")}
    assert [
        api_types.TrialComponentMetricSummary(
            metric_name="J", count=1, min=1.0, max=2.0, avg=3.0, std_dev=4.0, source_arn="K", timestamp=now
        )
    ]


def test_list(sagemaker_boto_client):
    start_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    creation_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
    last_modified_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=4)

    sagemaker_boto_client.list_trial_components.side_effect = [
        {
            "TrialComponentSummaries": [
                {
                    "TrialComponentName": "A" + str(i),
                    "TrialComponentArn": "B" + str(i),
                    "DisplayName": "C" + str(i),
                    "SourceArn": "D" + str(i),
                    "Status": {"PrimaryStatus": "InProgress", "Message": "E" + str(i)},
                    "StartTime": start_time + datetime.timedelta(hours=i),
                    "EndTime": end_time + datetime.timedelta(hours=i),
                    "CreationTime": creation_time + datetime.timedelta(hours=i),
                    "LastModifiedTime": last_modified_time + datetime.timedelta(hours=i),
                    "LastModifiedBy": {},
                }
                for i in range(10)
            ],
            "NextToken": "100",
        },
        {
            "TrialComponentSummaries": [
                {
                    "TrialComponentName": "A" + str(i),
                    "TrialComponentArn": "B" + str(i),
                    "DisplayName": "C" + str(i),
                    "SourceArn": "D" + str(i),
                    "Status": {"PrimaryStatus": "InProgress", "Message": "E" + str(i)},
                    "StartTime": start_time + datetime.timedelta(hours=i),
                    "EndTime": end_time + datetime.timedelta(hours=i),
                    "CreationTime": creation_time + datetime.timedelta(hours=i),
                    "LastModifiedTime": last_modified_time + datetime.timedelta(hours=i),
                    "LastModifiedBy": {},
                }
                for i in range(10, 20)
            ]
        },
    ]

    expected = [
        api_types.TrialComponentSummary(
            trial_component_name="A" + str(i),
            trial_component_arn="B" + str(i),
            display_name="C" + str(i),
            source_arn="D" + str(i),
            status=api_types.TrialComponentStatus(primary_status="InProgress", message="E" + str(i)),
            start_time=start_time + datetime.timedelta(hours=i),
            end_time=end_time + datetime.timedelta(hours=i),
            creation_time=creation_time + datetime.timedelta(hours=i),
            last_modified_time=last_modified_time + datetime.timedelta(hours=i),
            last_modified_by={},
        )
        for i in range(20)
    ]
    result = list(
        trial_component.TrialComponent.list(
            sagemaker_boto_client=sagemaker_boto_client,
            source_arn="foo",
            sort_by="CreationTime",
            sort_order="Ascending",
        )
    )

    assert expected == result
    expected_calls = [
        unittest.mock.call(SortBy="CreationTime", SortOrder="Ascending", SourceArn="foo"),
        unittest.mock.call(NextToken="100", SortBy="CreationTime", SortOrder="Ascending", SourceArn="foo"),
    ]
    assert expected_calls == sagemaker_boto_client.list_trial_components.mock_calls


def test_list_empty(sagemaker_boto_client):
    sagemaker_boto_client.list_trial_components.return_value = {"TrialComponentSummaries": []}
    assert [] == list(trial_component.TrialComponent.list(sagemaker_boto_client=sagemaker_boto_client))


def test_list_trial_components_call_args(sagemaker_boto_client):
    created_before = datetime.datetime(1999, 10, 12, 0, 0, 0)
    created_after = datetime.datetime(1990, 10, 12, 0, 0, 0)
    trial_name = "foo-trial"
    experiment_name = "foo-experiment"
    next_token = "thetoken"
    max_results = 99

    sagemaker_boto_client.list_trial_components.return_value = {}
    assert [] == list(
        trial_component.TrialComponent.list(
            sagemaker_boto_client=sagemaker_boto_client,
            trial_name=trial_name,
            experiment_name=experiment_name,
            created_before=created_before,
            created_after=created_after,
            next_token=next_token,
            max_results=max_results,
            sort_by="CreationTime",
            sort_order="Ascending",
        )
    )

    expected_calls = [
        unittest.mock.call(
            TrialName="foo-trial",
            ExperimentName="foo-experiment",
            CreatedBefore=created_before,
            CreatedAfter=created_after,
            SortBy="CreationTime",
            SortOrder="Ascending",
            NextToken="thetoken",
            MaxResults=99,
        )
    ]
    assert expected_calls == sagemaker_boto_client.list_trial_components.mock_calls


def test_search(sagemaker_boto_client):
    sagemaker_boto_client.search.return_value = {
        "Results": [
            {
                "TrialComponent": {
                    "TrialComponentName": "tc-1",
                    "TrialComponentArn": "arn::tc-1",
                    "DisplayName": "TC1",
                }
            },
            {
                "TrialComponent": {
                    "TrialComponentName": "tc-2",
                    "TrialComponentArn": "arn::tc-2",
                    "DisplayName": "TC2",
                }
            },
        ]
    }
    expected = [
        api_types.TrialComponentSearchResult(
            trial_component_name="tc-1", trial_component_arn="arn::tc-1", display_name="TC1"
        ),
        api_types.TrialComponentSearchResult(
            trial_component_name="tc-2", trial_component_arn="arn::tc-2", display_name="TC2"
        ),
    ]
    assert expected == list(trial_component.TrialComponent.search(sagemaker_boto_client=sagemaker_boto_client))


def test_save(sagemaker_boto_client):
    obj = trial_component.TrialComponent(
        sagemaker_boto_client,
        trial_component_name="foo",
        display_name="bar",
        parameters_to_remove=["E"],
        input_artifacts_to_remove=["F"],
        output_artifacts_to_remove=["G"],
    )
    sagemaker_boto_client.update_trial_component.return_value = {}
    obj.save()

    sagemaker_boto_client.update_trial_component.assert_called_with(
        TrialComponentName="foo",
        DisplayName="bar",
        ParametersToRemove=["E"],
        InputArtifactsToRemove=["F"],
        OutputArtifactsToRemove=["G"],
    )


def test_delete(sagemaker_boto_client):
    obj = trial_component.TrialComponent(sagemaker_boto_client, trial_component_name="foo", display_name="bar")
    sagemaker_boto_client.delete_trial_component.return_value = {}
    obj.delete()
    sagemaker_boto_client.delete_trial_component.assert_called_with(TrialComponentName="foo")


def test_delete_with_force_disassociate(sagemaker_boto_client):
    obj = trial_component.TrialComponent(sagemaker_boto_client, trial_component_name="foo", display_name="bar")
    sagemaker_boto_client.delete_trial_component.return_value = {}

    sagemaker_boto_client.list_trials.side_effect = [
        {"TrialSummaries": [{"TrialName": "trial-1"}, {"TrialName": "trial-2"}], "NextToken": "a"},
        {"TrialSummaries": [{"TrialName": "trial-3"}, {"TrialName": "trial-4"}]},
    ]

    obj.delete(force_disassociate=True)
    expected_calls = [
        unittest.mock.call(TrialName="trial-1", TrialComponentName="foo"),
        unittest.mock.call(TrialName="trial-2", TrialComponentName="foo"),
        unittest.mock.call(TrialName="trial-3", TrialComponentName="foo"),
        unittest.mock.call(TrialName="trial-4", TrialComponentName="foo"),
    ]
    assert expected_calls == sagemaker_boto_client.disassociate_trial_component.mock_calls
    sagemaker_boto_client.delete_trial_component.assert_called_with(TrialComponentName="foo")


def test_boto_ignore():
    obj = trial_component.TrialComponent(sagemaker_boto_client, trial_component_name="foo", display_name="bar")
    assert obj._boto_ignore() == ["ResponseMetadata", "CreatedBy"]
