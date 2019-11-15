import base64
import glob
import signal
import subprocess
import sys

from contextlib import contextmanager

import docker
import botocore

from tests.fixtures import *
from tests.helpers import *

from smexperiments import api_types


@pytest.fixture(scope='session')
def training_docker_image():
    client = docker.from_env()
    ecr_client = boto3.client('ecr', region_name='us-west-2')
    token = ecr_client.get_authorization_token()
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    registry = token['authorizationData'][0]['proxyEndpoint']

    subprocess.check_call([sys.executable, 'setup.py', 'sdist'])
    [sdist_path] = glob.glob('dist/smexperiments*')
    shutil.copy(sdist_path, 'tests/integ-jobs/docker/smexperiments-1.0.0.tar.gz')

    if not os.path.exists('tests/integ-jobs/docker/boto'):
        os.makedirs('tests/integ-jobs/docker/boto')
    shutil.copy('boto/sagemaker-experiments-2017-07-24.normal.json', 'tests/integ-jobs/docker/boto/sagemaker-experiments-2017-07-24.normal.json')
    repository_name = "smexperiments-test"
    try:
        ecr_client.create_repository(repositoryName=repository_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryAlreadyExistsException':
            pass
        else:
            raise

    tag = '{}/{}:{}'.format(registry, repository_name, '1.0.0')[8:]

    # pull existing image for layer cache
    try:
        client.images.pull(tag, auth_config={'username': username, 'password': password})
    except docker.errors.NotFound:
        pass
    client.images.build(
        path='tests/integ-jobs/docker',
        dockerfile='Dockerfile',
        tag=tag,
        cache_from=[tag],
        buildargs={'library': 'smexperiments-1.0.0.tar.gz',
                   'botomodel': 'boto/sagemaker-experiments-2017-07-24.normal.json',
                   'script': 'scripts/script.py',
                   'endpoint': os.environ.get('SAGEMAKER_ENDPOINT', '')})
    client.images.push(tag, auth_config={'username': username, 'password': password})
    return tag


@contextmanager
def timeout(seconds=0, minutes=0, hours=0):
    """
    Add a signal-based timeout to any block of code.
    If multiple time units are specified, they will be added together to determine time limit.
    Usage:
    with timeout(seconds=5):
        my_slow_function(...)
    Args:
        - seconds: The time limit, in seconds.
        - minutes: The time limit, in minutes.
        - hours: The time limit, in hours.
    """

    limit = seconds + 60 * minutes + 3600 * hours

    def handler(signum, frame):
        raise TimeoutError('timed out after {} seconds'.format(limit))

    try:
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(limit)

        yield
    finally:
        signal.alarm(0)


def dump_logs(job):
    logs = boto3.client('logs')
    [log_stream] = logs.describe_log_streams(logGroupName="/aws/sagemaker/TrainingJobs",
                                             logStreamNamePrefix=job)['logStreams']
    log_stream_name = log_stream['logStreamName']
    next_token = None
    while True:
        if next_token:
            log_event_response = logs.get_log_events(
                logGroupName="/aws/sagemaker/TrainingJobs",
                logStreamName=log_stream_name,
                nextToken=next_token)
        else:
            log_event_response = logs.get_log_events(
                logGroupName="/aws/sagemaker/TrainingJobs",
                logStreamName=log_stream_name)
        next_token = log_event_response['nextForwardToken']
        events = log_event_response['events']
        if not events:
            break
        for event in events:
            print (event['message'])


def wait_for_job(job, sagemaker_client):
    with timeout(minutes=15):
        while True:
            response = sagemaker_client.describe_training_job(TrainingJobName=job)
            status = response['TrainingJobStatus']
            if status == 'Failed':
                print(response)
                dump_logs(job)
                pytest.fail('Training job failed: ' + job)
            if status == 'Completed':
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(30)


def test_track_from_training_job(sagemaker_boto_client, training_job_name):
    tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)
    source_arn = tj['TrainingJobArn']
    wait_for_job(training_job_name, sagemaker_boto_client)
    tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)

    trial_component_name = list(trial_component.TrialComponent.\
                                list(source_arn=source_arn,
                                     sagemaker_boto_client=sagemaker_boto_client))[0].trial_component_name

    def validate():
        tj = sagemaker_boto_client.describe_training_job(TrainingJobName=training_job_name)
        trial_component_obj = trial_component.TrialComponent.load(trial_component_name=trial_component_name,
                                                                  sagemaker_boto_client=sagemaker_boto_client)
        print(tj)
        assert source_arn == trial_component_obj.source.source_arn
        assert to_seconds(tj['TrainingStartTime']) == to_seconds(trial_component_obj.start_time)
        assert to_seconds(tj['TrainingEndTime']) == to_seconds(trial_component_obj.end_time)
        assert trial_component_obj.parameters.items() >= {
            'InstanceCount': 1.0,
            'InstanceType': 'ml.m5.large',
            'p1': 1.0
        }.items()
        assert trial_component_obj.input_artifacts.items() >= {
            'TrainingImage': api_types.TrialComponentArtifact(value=tj['AlgorithmSpecification']['TrainingImage']),
            'train': api_types.TrialComponentArtifact(value=tj['InputDataConfig'][0]['DataSource']['S3DataSource']['S3Uri'])
        }.items()
        assert trial_component_obj.output_artifacts.items() >= {
            'ModelArtifact': api_types.TrialComponentArtifact(value=tj['ModelArtifacts']['S3ModelArtifacts'])
        }.items()
        metrics = trial_component_obj.metrics
        for metric_summary in metrics:
            assert metric_summary.count == 2
            assert metric_summary.min == 0.0
            assert metric_summary.max == 1.0
        assert 4 == len(metrics)

        # Currently broken
        # assert trial_component_obj.status.primary_status == 'Completed'

    try:
        retry(lambda: dump_logs(training_job_name))
    except:
        pass  # best effort attempt to print logs, there may be no logs if script didn't print anything
    retry(validate)


def to_seconds(dt):
    return int(dt.timestamp())
