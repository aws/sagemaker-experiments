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
import unittest.mock
import pytest
import shutil
import tempfile
import os
import datetime
from smexperiments import api_types, tracker, trial_component, metrics

@pytest.fixture
def boto3_session():
    mocked = unittest.mock.Mock()
    mocked.client().return_value.get_caller_identity.return_value = {'Account': unittest.mock.Mock()}
    return mocked


@pytest.fixture
def tempdir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)


@pytest.fixture
def sagemaker_boto_client(boto3_session):
    return boto3_session.client('sagemaker')


@pytest.fixture
def source_arn():
    return 'source_arn'


@pytest.fixture
def environ(source_arn):
    with unittest.mock.patch('os.environ') as environ:
        def get_side_effect(key):
            if key == tracker.TRAINING_JOB_ARN_ENV:
                return source_arn

        def contains_side_effect(key):
            if key == tracker.TRAINING_JOB_ARN_ENV:
                return True

        environ.__contains__.side_effect = contains_side_effect
        environ.get.side_effect = get_side_effect
        yield environ


def test_resolve_trial_component_for_job(environ, source_arn, sagemaker_boto_client):
    trial_component_name = 'foo-trial_component_name'
    sagemaker_boto_client.list_trial_components.return_value = {
        'TrialComponentSummaries': [{'TrialComponentName': trial_component_name}]
    }
    sagemaker_boto_client.describe_trial_component.return_value = {'TrialComponentName': trial_component_name}
    trial_component = tracker._resolve_trial_component_for_job(sagemaker_boto_client)
    sagemaker_boto_client.list_trial_components.assert_called_with(SourceArn=source_arn)
    sagemaker_boto_client.describe_trial_component.assert_called_with(TrialComponentName=trial_component_name)

    assert trial_component_name == trial_component.trial_component_name


@unittest.mock.patch('os.environ')
def test_resolve_trial_component_for_job_no_env(mocked_environ, sagemaker_boto_client):
    mocked_environ.__contains__.side_efect = lambda x: False
    assert None == tracker._resolve_trial_component_for_job(sagemaker_boto_client)


@unittest.mock.patch('time.sleep')
def test_resolve_trial_component_for_job_sleep(mocked_sleep, environ, sagemaker_boto_client):
    trial_component_name = 'foo-trial_component_name'
    sagemaker_boto_client.list_trial_components.side_effect = [
        {'TrialComponentSummaries': []},
        {'TrialComponentSummaries':[{'TrialComponentName': trial_component_name}]}
    ]
    sagemaker_boto_client.describe_trial_component.return_value = {'TrialComponentName': trial_component_name}
    trial_component = tracker._resolve_trial_component_for_job(sagemaker_boto_client)
    assert trial_component_name == trial_component.trial_component_name
    mocked_sleep.assert_called_with(tracker.RESOLVE_JOB_INTERVAL_SECONDS)


@unittest.mock.patch('time.sleep')
@unittest.mock.patch('time.time')
def test_resolve_trial_component_for_job_timeout(mocked_time, mocked_sleep, environ, sagemaker_boto_client):
    sagemaker_boto_client.list_trial_components.return_value = {'TrialComponentSummaries': []}
    mocked_time.side_effect = [0, 1, tracker.RESOLVE_JOB_TIMEOUT_SECONDS + 1]
    assert None == tracker._resolve_trial_component_for_job(sagemaker_boto_client)


@unittest.mock.patch('smexperiments.tracker._resolve_trial_component_for_job')
def test_load_in_sagemaker_job(mocked_rtcfj, boto3_session, sagemaker_boto_client):
    tc = trial_component.TrialComponent(trial_component_name='foo', sagemaker_boto_client=sagemaker_boto_client)
    mocked_rtcfj.return_value = tc
    tracker_obj = tracker.Tracker.load(boto3_session=boto3_session)
    assert tc == tracker_obj._trial_component
    assert isinstance(tracker_obj._metrics_writer, metrics.SageMakerFileMetricsWriter)


@unittest.mock.patch('smexperiments.tracker._resolve_trial_component_for_job')
def test_load_in_sagemaker_job_no_resolved_tc(mocked_rtcfj, boto3_session, sagemaker_boto_client):
    mocked_rtcfj.return_value = None
    with pytest.raises(ValueError):
        tracker.Tracker.load(boto3_session=boto3_session)


def test_load(boto3_session, sagemaker_boto_client):
    trial_component_name = 'foo-trial-component'
    sagemaker_boto_client.describe_trial_component.return_value = {
        'TrialComponentName': trial_component_name
    }
    assert trial_component_name == tracker.Tracker.load(
        trial_component_name=trial_component_name, boto3_session=boto3_session)._trial_component.trial_component_name


@pytest.fixture
def trial_component_obj(sagemaker_boto_client):
    return trial_component.TrialComponent(sagemaker_boto_client)


@pytest.fixture
def under_test(trial_component_obj):
    return tracker.Tracker(trial_component_obj, unittest.mock.Mock(), unittest.mock.Mock())


def test_log_parameter(under_test):
    under_test.log_parameter('foo', 'bar')
    assert under_test._trial_component.parameters['foo'] == 'bar'
    under_test.log_parameter('whizz', 1)
    assert under_test._trial_component.parameters['whizz'] == 1


def test_enter(under_test):
    under_test.__enter__()
    assert isinstance(under_test._trial_component.start_time, datetime.datetime)
    assert under_test._trial_component.status.primary_status == 'InProgress'


def test_cm(sagemaker_boto_client, under_test):
    sagemaker_boto_client.update_trial_component.return_value = {}
    with under_test:
        pass
    assert under_test._trial_component.status.primary_status == 'Completed'
    assert isinstance(under_test._trial_component.end_time, datetime.datetime)


def test_cm_fail(sagemaker_boto_client, under_test):
    sagemaker_boto_client.update_trial_component.return_value = {}
    try:
        with under_test:
            raise ValueError('Foo')
    except ValueError:
        pass

    assert under_test._trial_component.status.primary_status == 'Failed'
    assert under_test._trial_component.status.message
    assert isinstance(under_test._trial_component.end_time, datetime.datetime)


def test_enter_sagemaker_job(sagemaker_boto_client, under_test):
    sagemaker_boto_client.update_trial_component.return_value = {}
    under_test._in_sagemaker_job = True
    with under_test:
        pass
    assert under_test._trial_component.start_time is None
    assert under_test._trial_component.end_time is None
    assert under_test._trial_component.status is None


def test_log_parameters(under_test):
    under_test.log_parameters({'a':'b', 'c':'d', 'e':5})
    assert under_test._trial_component.parameters == {
        'a': 'b',
        'c': 'd',
        'e': 5
    }


def test_log_input(under_test):
    under_test.log_input('foo', 'baz', 'text/text')
    assert under_test._trial_component.input_artifacts == {
        'foo': api_types.TrialComponentArtifact(value='baz', media_type='text/text')
    }


def test_log_output(under_test):
    under_test.log_output('foo', 'baz', 'text/text')
    assert under_test._trial_component.output_artifacts == {
        'foo': api_types.TrialComponentArtifact(value='baz', media_type='text/text')
    }


def test_log_metric(under_test):
    now = datetime.datetime.now()
    under_test.log_metric('foo', 1.0, 1, now)
    under_test._metrics_writer.log_metric.assert_called_with('foo', 1.0, 1, now)


def test_log_artifact(under_test):
    under_test.log_artifact('foo.txt', 'name', 'whizz/bang')
    under_test._artifact_uploader.upload_artifact.assert_called_with('foo.txt', 'name')
    assert 'whizz/bang' == under_test._trial_component.output_artifacts['name'].media_type

    under_test.log_artifact('foo.txt')
    under_test._artifact_uploader.upload_artifact.assert_called_with('foo.txt', 'foo.txt')
    assert 'foo.txt' in under_test._trial_component.output_artifacts
    assert 'text/plain' == under_test._trial_component.output_artifacts['foo.txt'].media_type


def test_resolve_artifact_name():
    file_names = {
        'a':'a',
        'a.txt':'a.txt',
        'b.':'b.',
        '.c':'.c',
        '/x/a/a.txt':'a.txt',
        '/a/b/c.':'c.',
        './.a':'.a',
        '../b.txt':'b.txt',
        '~/a.txt':'a.txt',
        'c/d.txt':'d.txt'
    }
    for file_name, artifact_name in file_names.items():
        assert artifact_name == tracker._resolve_artifact_name(file_name)


@pytest.fixture
def artifact_uploader(boto3_session):
    return tracker._ArtifactUploader('trial_component_name', 'artifact_bucket', 'artifact_prefix', boto3_session)


def test_artifact_uploader_init(artifact_uploader):
    assert 'trial_component_name' == artifact_uploader.trial_component_name
    assert 'artifact_bucket' == artifact_uploader.artifact_bucket
    assert 'artifact_prefix' == artifact_uploader.artifact_prefix


def test_artifact_uploader_upload_artifact_file_not_exists(tempdir, artifact_uploader):
    not_exist_file = os.path.join(tempdir, 'not.exists')
    with pytest.raises(ValueError):
        artifact_uploader.upload_artifact(not_exist_file, 'not.exists')


def test_artifact_uploader_s3(tempdir, artifact_uploader):
    path = os.path.join(tempdir, 'exists')
    with open(path, 'a') as f:
        f.write('boo')

    name = tracker._resolve_artifact_name(path)
    s3_uri = artifact_uploader.upload_artifact(path, name)
    expected_key = '{}/{}/{}'.format(artifact_uploader.artifact_prefix, artifact_uploader.trial_component_name, name)

    artifact_uploader.s3_client.upload_file.assert_called_with(
        path, artifact_uploader.artifact_bucket, expected_key)

    expected_uri = 's3://{}/{}'.format(artifact_uploader.artifact_bucket, expected_key)
    assert expected_uri == s3_uri


def test_guess_media_type():
    assert 'text/plain' == tracker._guess_media_type('foo.txt')
