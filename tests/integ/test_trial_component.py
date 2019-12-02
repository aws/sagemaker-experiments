import datetime
from tests.fixtures import *

from smexperiments import api_types, trial_component


def test_create_delete(trial_component_obj):
    # Fixture does create / delete, just need to ensure called at least once
    assert trial_component_obj.trial_component_name


def test_save(trial_component_obj, sagemaker_boto_client):
    trial_component_obj.display_name = str(uuid.uuid4())
    trial_component_obj.status = api_types.TrialComponentStatus(primary_status='InProgress', message='Message')
    trial_component_obj.start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    trial_component_obj.end_time = datetime.datetime.now(datetime.timezone.utc)
    trial_component_obj.parameters = {
        'foo': 'bar',
        'whizz': 100.1
    }
    trial_component_obj.input_artifacts = {
        'snizz': api_types.TrialComponentArtifact(value='s3:/foo/bar', media_type='text/plain')
    }
    trial_component_obj.output_artifacts = {
        'fly': api_types.TrialComponentArtifact(value='s3:/sky/far', media_type='away/tomorrow')
    }
    trial_component_obj.save()

    loaded = trial_component.TrialComponent.load(trial_component_name = trial_component_obj.trial_component_name,
                                                 sagemaker_boto_client=sagemaker_boto_client)

    assert trial_component_obj.trial_component_name == loaded.trial_component_name
    assert trial_component_obj.status == loaded.status

    assert trial_component_obj.start_time - loaded.start_time < datetime.timedelta(seconds=1)
    assert trial_component_obj.end_time - loaded.end_time < datetime.timedelta(seconds=1)

    assert trial_component_obj.parameters == loaded.parameters
    assert trial_component_obj.input_artifacts == loaded.input_artifacts
    assert trial_component_obj.output_artifacts == loaded.output_artifacts


def test_load(trial_component_obj, sagemaker_boto_client):
    loaded = trial_component.TrialComponent.load(trial_component_name=trial_component_obj.trial_component_name,
                                                 sagemaker_boto_client=sagemaker_boto_client)
    assert trial_component_obj.trial_component_arn == loaded.trial_component_arn


def test_list_sort(trial_components, sagemaker_boto_client):
    slack = datetime.timedelta(minutes=1)
    now = datetime.datetime.now(datetime.timezone.utc)
    trial_component_names = [tc.trial_component_name for tc in trial_components]

    for sort_order in ['Ascending', 'Descending']:
        trial_component_names_listed = [s.trial_component_name for s in trial_component.TrialComponent.list(
            created_after=now - slack,
            created_before=now + slack,
            sort_by='CreationTime',
            sort_order=sort_order,
            sagemaker_boto_client=sagemaker_boto_client
        ) if s.trial_component_name in trial_component_names]

    if sort_order == 'Descending':
        trial_component_names_listed = trial_component_names_listed[::-1]
    assert trial_component_names == trial_component_names_listed
    assert trial_component_names # sanity test
