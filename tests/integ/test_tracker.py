from tests.fixtures import *
from tests.helpers import *
from smexperiments import tracker, trial_component, _utils


def test_load_trial_component(trial_component_obj, sagemaker_boto_client):
    tracker_obj = tracker.Tracker.load(trial_component_name=trial_component_obj.trial_component_name,
                                       sagemaker_boto_client=sagemaker_boto_client)
    assert tracker_obj
    assert tracker_obj._trial_component.trial_component_name == trial_component_obj.trial_component_name


def test_load_trial_component_fails(sagemaker_boto_client):
    with pytest.raises(ValueError):
        tracker.Tracker.load(sagemaker_boto_client=sagemaker_boto_client)


def test_load_trial_component_mock_training_job(sagemaker_boto_client):
    # Update os environ
    training_job_name = 'smexperiments-integ-2d138285-f0d3-48be-ad1e-0296058876d0'
    training_job_arn = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)['TrainingJobArn']

    old_value = os.environ.get(tracker.TRAINING_JOB_ARN_ENV)
    try:
        os.environ[tracker.TRAINING_JOB_ARN_ENV] = training_job_arn
        tracker_obj = tracker.Tracker.load(sagemaker_boto_client=sagemaker_boto_client)
        assert tracker_obj._trial_component
    finally:
        if old_value is not None:
            os.environ[tracker.TRAINING_JOB_ARN_ENV] = old_value
        else:
            del os.environ[tracker.TRAINING_JOB_ARN_ENV]


def test_create(sagemaker_boto_client):
    tracker_obj = tracker.Tracker.create(sagemaker_boto_client=sagemaker_boto_client)
    try:
        sagemaker_boto_client.describe_trial_component(
            TrialComponentName=tracker_obj._trial_component.trial_component_name
        )
    finally:
        tracker_obj._trial_component.delete()


def test_create_display_name(sagemaker_boto_client):
    display_name = name()
    tracker_obj = tracker.Tracker.create(display_name=display_name, sagemaker_boto_client=sagemaker_boto_client)
    try:
        assert display_name == tracker_obj._trial_component.display_name
    finally:
        tracker_obj._trial_component.delete()


def test_log_simple(trial_component_obj, sagemaker_boto_client):
    with tracker.Tracker.load(trial_component_obj.trial_component_name,
                              sagemaker_boto_client=sagemaker_boto_client) as tracker_obj:
        tracker_obj.log_parameter('p1', 1.0)
        tracker_obj.log_parameter('p2', 'p2-value')
        tracker_obj.log_parameters({
            'p3': 2.0,
            'p4': 'p4-value'
        })
    loaded_obj = trial_component.TrialComponent.load(trial_component_name=trial_component_obj.trial_component_name,
                                                     sagemaker_boto_client=sagemaker_boto_client)
    expected_parameters = {
        'p1': 1.0,
        'p2': 'p2-value',
        'p3': 2.0,
        'p4': 'p4-value'
    }
    assert expected_parameters == loaded_obj.parameters


def test_log_artifact(trial_component_obj, bucket, tempdir, sagemaker_boto_client):
    prefix = name()
    file_contents = 'happy monkey monkey'
    file_path = os.path.join(tempdir, 'foo.txt')
    artifact_name = 'monkey-monkey'
    with open(file_path, 'w') as foo_file:
        foo_file.write(file_contents)

    with tracker.Tracker.load(trial_component_obj.trial_component_name,
                              artifact_bucket=bucket, artifact_prefix=prefix,
                              sagemaker_boto_client=sagemaker_boto_client) as tracker_obj:
        tracker_obj.log_artifact(file_path, name=artifact_name)

    loaded = trial_component.TrialComponent.load(trial_component_name=trial_component_obj.trial_component_name,
                                                 sagemaker_boto_client=sagemaker_boto_client)
    assert 'text/plain' == loaded.output_artifacts[artifact_name].media_type
    assert prefix in loaded.output_artifacts[artifact_name].value


def test_create_default_bucket(boto3_session):
    bucket_name_prefix=_utils.name('sm-test')
    bucket = _utils.get_or_create_default_bucket(boto3_session, default_bucket_prefix=bucket_name_prefix)
    s3_client = boto3_session.client('s3')
    try:
        s3_client.head_bucket(Bucket=bucket)
    finally:
        s3_client.delete_bucket(Bucket=bucket)


def test_log_metric(trial_component_obj, sagemaker_boto_client):
    metric_name = name()
    N = 25
    with tracker.Tracker.load(trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client)\
            as tracker_obj:
        for i in range(N):
            tracker_obj.log_metric(metric_name, i)
    expect_stat(sagemaker_boto_client, trial_component_obj.trial_component_arn, metric_name, 'Count', N)
