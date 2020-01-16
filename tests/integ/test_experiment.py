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

from tests.helpers import name
from smexperiments import experiment, trial


def test_create_delete(experiment_obj):
    # The fixture creates deletes, just ensure fixture is used at least once
    assert experiment_obj.experiment_name


def test_save(experiment_obj):
    description = name()
    experiment_obj.description = description
    experiment_obj.save()


def test_save_load(experiment_obj, sagemaker_boto_client):
    experiment_obj_two = experiment.Experiment.load(
        experiment_name=experiment_obj.experiment_name, sagemaker_boto_client=sagemaker_boto_client
    )
    assert experiment_obj.experiment_name == experiment_obj_two.experiment_name
    assert experiment_obj.description == experiment_obj_two.description

    experiment_obj.description = name()
    experiment_obj.display_name = name()
    experiment_obj.save()
    experiment_obj_three = experiment.Experiment.load(
        experiment_name=experiment_obj.experiment_name, sagemaker_boto_client=sagemaker_boto_client
    )
    assert experiment_obj.description == experiment_obj_three.description
    assert experiment_obj.display_name == experiment_obj_three.display_name


def test_list(sagemaker_boto_client, experiments):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)
    experiment_names_listed = [
        s.experiment_name
        for s in experiment.Experiment.list(
            created_after=now - slack, created_before=now + slack, sagemaker_boto_client=sagemaker_boto_client
        )
    ]
    for experiment_obj in experiments:
        assert experiment_obj.experiment_name in experiment_names_listed
    assert experiment_names_listed  # sanity test


def test_list_sort(sagemaker_boto_client, experiments):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)

    for sort_order in ["Ascending", "Descending"]:
        experiment_names_listed = [
            s.experiment_name
            for s in experiment.Experiment.list(
                created_after=now - slack,
                created_before=now + slack,
                sort_by="CreationTime",
                sort_order=sort_order,
                sagemaker_boto_client=sagemaker_boto_client,
            )
        ]
    experiment_names = [experiment_obj.experiment_name for experiment_obj in experiments]

    # Restrict the listed names to just be the ones we created.
    # Reverse returned list based on sort order
    # Assert that the list contains the same names in the same order as what we created
    experiment_names_listed = [name for name in experiment_names_listed if name in experiment_names]
    if sort_order == "Descending":
        experiment_names_listed = experiment_names_listed[::-1]
    assert experiment_names == experiment_names_listed
    assert experiment_names  # sanity test


def test_create_trial(experiment_obj, sagemaker_boto_client):
    trial_obj = experiment_obj.create_trial()
    try:
        loaded_trial_obj = trial.Trial.load(
            trial_name=trial_obj.trial_name, sagemaker_boto_client=sagemaker_boto_client
        )
        assert trial_obj.trial_name == loaded_trial_obj.trial_name
        assert trial_obj.experiment_name == loaded_trial_obj.experiment_name

    finally:
        trial_obj.delete()


def test_list_trials(experiment_obj, trials):
    # This relies on the fact that the experiment_obj fixture was passed to the fixture that created the trials
    trial_names = [trial_obj.trial_name for trial_obj in trials]
    assert set(trial_names) == set([s.trial_name for s in experiment_obj.list_trials()])
    assert trial_names  # sanity test
