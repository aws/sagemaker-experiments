import datetime

from tests.fixtures import *

def test_create_delete(trial_obj):
    # Fixture creates / deletes, just ensure used at least once.
    assert trial_obj.trial_name


def test_list(trials, sagemaker_boto_client):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)
    trial_names_listed = [s.trial_name
                          for s in trial.Trial.list(created_after=now - slack,
                                                    created_before=now + slack,
                                                    sagemaker_boto_client=sagemaker_boto_client)]
    for trial_obj in trials:
        assert trial_obj.trial_name in trial_names_listed
    assert trial_names_listed  # sanity test


def test_list_sort(trials, sagemaker_boto_client):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)
    for sort_order in ['Ascending', 'Descending']:
        trial_names_listed = [s.trial_name
                              for s in trial.Trial.list(created_after=now - slack,
                                                        created_before=now + slack,
                                                        sort_by='CreationTime',
                                                        sort_order=sort_order,
                                                        sagemaker_boto_client=sagemaker_boto_client)]
        if sort_order == 'Descending':
            trial_names_listed = trial_names_listed[::-1]

        trial_names_created = [trial_obj.trial_name for trial_obj in trials]
        trial_names_listed = [trial_name for trial_name in trial_names_listed if trial_name in trial_names_created]
        assert trial_names_created == trial_names_listed

        assert trial_names_listed  # sanity test


def test_add_remove_trial_component(trial_obj, trial_component_obj):
    trial_obj.add_trial_component(trial_component_obj)
    trial_components = list(trial_obj.list_trial_components())
    trial_components = [s.trial_component_name for s in trial_components]
    assert [trial_component_obj.trial_component_name] == trial_components

    trial_obj.remove_trial_component(trial_component_obj)
    trial_components = list(trial_obj.list_trial_components())
    assert [] == trial_components


def test_list_trial_components(trial_obj, trial_components):
    for trial_component_obj in trial_components:
        trial_obj.add_trial_component(trial_component_obj)
    try:
        trial_component_names = [trial_component_obj.trial_component_name for trial_component_obj in trial_components]
        listed_trial_component_names = [s.trial_component_name for s in trial_obj.list_trial_components()]
        assert set(trial_component_names) == set(listed_trial_component_names)
        assert listed_trial_component_names  # sanity test
    finally:
        for trial_component_obj in trial_components:
            trial_obj.remove_trial_component(trial_component_obj)


def test_save(trial_obj, sagemaker_boto_client):
    trial_obj.display_name = 'foo'
    trial_obj.save()
    assert 'foo' == trial.Trial.load(trial_name=trial_obj.trial_name).display_name
