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

import datetime

from smexperiments import trial
from smexperiments.search_expression import SearchExpression, Filter, Operator


def test_create_delete(trial_obj):
    # Fixture creates / deletes, just ensure used at least once.
    assert trial_obj.trial_name


def test_create_tags(trial_obj, sagemaker_boto_client):
    while True:
        actual_tags = sagemaker_boto_client.list_tags(ResourceArn=trial_obj.trial_arn)["Tags"]
        if actual_tags:
            break
    for tag in actual_tags:
        if "aws:tag" in tag.get("Key"):
            actual_tags.remove(tag)
    assert actual_tags == trial_obj.tags


def test_list(trials, sagemaker_boto_client):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)
    trial_names_listed = [
        s.trial_name
        for s in trial.Trial.list(
            created_after=now - slack, created_before=now + slack, sagemaker_boto_client=sagemaker_boto_client
        )
    ]
    for trial_obj in trials:
        assert trial_obj.trial_name in trial_names_listed
    assert trial_names_listed  # sanity test


def test_list_with_trial_component(trials, trial_component_obj, sagemaker_boto_client):
    trial_with_component = trials[0]
    trial_with_component.add_trial_component(trial_component_obj)

    trial_listed = [
        s.trial_name
        for s in trial.Trial.list(
            trial_component_name=trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
        )
    ]
    assert len(trial_listed) == 1
    assert trial_with_component.trial_name == trial_listed[0]
    # clean up
    trial_with_component.remove_trial_component(trial_component_obj)
    assert trial_listed


def test_list_sort(trials, sagemaker_boto_client):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)
    for sort_order in ["Ascending", "Descending"]:
        trial_names_listed = [
            s.trial_name
            for s in trial.Trial.list(
                created_after=now - slack,
                created_before=now + slack,
                sort_by="CreationTime",
                sort_order=sort_order,
                sagemaker_boto_client=sagemaker_boto_client,
            )
        ]
        if sort_order == "Descending":
            trial_names_listed = trial_names_listed[::-1]

        trial_names_created = [trial_obj.trial_name for trial_obj in trials]
        trial_names_listed = [trial_name for trial_name in trial_names_listed if trial_name in trial_names_created]
        assert trial_names_created == trial_names_listed

        assert trial_names_listed  # sanity test


def test_search(sagemaker_boto_client):
    trial_names_searched = []
    search_filter = Filter(name="ExperimentName", operator=Operator.CONTAINS, value="smexperiments-integ-")
    search_expression = SearchExpression(filters=[search_filter])
    for s in trial.Trial.search(
        search_expression=search_expression, max_results=10, sagemaker_boto_client=sagemaker_boto_client
    ):
        trial_names_searched.append(s.trial_name)

    assert len(trial_names_searched) > 0
    assert trial_names_searched  # sanity test


def test_add_remove_trial_component(trial_obj, trial_component_obj):
    trial_obj.add_trial_component(trial_component_obj)
    trial_components = list(trial_obj.list_trial_components())
    assert 1 == len(trial_components)
    trial_obj.remove_trial_component(trial_component_obj)
    trial_components = list(trial_obj.list_trial_components())
    assert 0 == len(trial_components)


def test_save(trial_obj, sagemaker_boto_client):
    trial_obj.display_name = "foo"
    trial_obj.save()
    assert (
        "foo"
        == trial.Trial.load(trial_name=trial_obj.trial_name, sagemaker_boto_client=sagemaker_boto_client).display_name
    )
