import pytest

import botocore
import base64
import glob
import uuid
import boto3
import tempfile

import logging
import os
import shutil
import subprocess
import sys

import time

import docker

from smexperiments import experiment, trial, trial_component


@pytest.fixture
def sagemaker_boto_client():
    return boto3.client('sagemaker-experiments', endpoint_url=os.environ.get('SAGEMAKER_ENDPOINT'))


@pytest.fixture(scope='session')
def boto3_session():
    return boto3.Session()


def name():
    return 'smexperiments-integ-{}'.format(str(uuid.uuid4()))


@pytest.fixture
def tempdir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)


@pytest.fixture
def experiment_obj(sagemaker_boto_client):
    description = '{}-{}'.format('description', str(uuid.uuid4()))
    boto3.set_stream_logger('', logging.INFO)
    experiment_obj = experiment.Experiment.create(experiment_name=name(), description=description,
                                                  sagemaker_boto_client=sagemaker_boto_client)
    yield experiment_obj
    experiment_obj.delete()


@pytest.fixture
def trial_obj(sagemaker_boto_client, experiment_obj):
    trial_obj = trial.Trial.create(trial_name=name(),
                                   experiment_name=experiment_obj.experiment_name,
                                   sagemaker_boto_client=sagemaker_boto_client)
    yield trial_obj
    trial_obj.delete()


@pytest.fixture
def trial_component_obj(sagemaker_boto_client):
    trial_component_obj = trial_component.TrialComponent.create(trial_component_name=name(),
                                                                sagemaker_boto_client=sagemaker_boto_client)
    yield trial_component_obj
    trial_component_obj.delete()


N = 3


def names():
    return [
        'smexperiments-integ-{}'.format(str(uuid.uuid4())) for i in range(N)
    ]


@pytest.fixture
def trials(experiment_obj, sagemaker_boto_client):
    trial_objs = [
        trial.Trial.create(trial_name=trial_name,
                           experiment_name=experiment_obj.experiment_name,
                           sagemaker_boto_client=sagemaker_boto_client) for trial_name in names()
    ]
    yield trial_objs
    for trial_obj in trial_objs:
        trial_obj.delete()


@pytest.fixture
def experiments(sagemaker_boto_client):
    experiment_objs = [
        experiment.Experiment.create(experiment_name=experiment_name,
                                     sagemaker_boto_client=sagemaker_boto_client)
        for experiment_name in names()
    ]
    yield experiment_objs
    for experiment_obj in experiment_objs:
        experiment_obj.delete()


@pytest.fixture
def trial_components(sagemaker_boto_client):
    trial_component_objs = [
        trial_component.TrialComponent.create(trial_component_name=trial_component_name,
                                              sagemaker_boto_client=sagemaker_boto_client)
        for trial_component_name in names()
    ]
    yield trial_component_objs
    for trial_component_obj in trial_component_objs:
        trial_component_obj.delete()


@pytest.fixture
def trial_components_in_trial(sagemaker_boto_client, trial_obj):
    trial_components = [
        trial_component.TrialComponent.create(trial_component_name=trial_component_name,
                                              sagemaker_boto_client=sagemaker_boto_client)
        for trial_component_name in names()
    ]
    for trial_component_obj in trial_components:
        trial_obj.add_trial_component(trial_component_obj)
    yield trial_components
    for trial_component_obj in trial_components:
        trial_obj.remove_trial_component(trial_component_obj)
        trial_component_obj.delete()


@pytest.fixture(scope='session')
def training_role_arn(boto3_session):
    iam_client = boto3_session.client('iam')
    policy_string = """
        {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "sagemaker.amazonaws.com",
          "maeve.aws.internal",
          "ease.aws.internal"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}"""
    policy_string = ''.join(policy_string.split())  # strip all whitespace
    role_name = 'SMExperimentsIntegTestSageMakerRole'
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=policy_string
        )
    except Exception as ex:
        if 'exists' in str(ex):
            return iam_client.get_role(RoleName=role_name)['Role']['Arn']
        else:
            raise ex

    iam_client.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess')
    time.sleep(30)
    return response['Role']['Arn']


@pytest.fixture(scope='session')
def bucket(boto3_session):
    s3_client = boto3_session.client('s3')
    sts_client = boto3_session.client('sts')
    account = sts_client.get_caller_identity()['Account']

    bucket_name = 'sagemaker-experiments-integ-test-%s-%s' % (boto3_session.region_name, account)
    try:
        if boto3_session.region_name != 'us-east-1':
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': boto3_session.region_name
                }
            )
        else:
            s3_client.create_bucket(
                Bucket=bucket_name
            )
    except Exception as ex:
        if 'BucketAlreadyOwnedByYou' in str(ex) or 'BucketAlreadyExists' in str(ex):
            return bucket_name
        raise ex
    return bucket_name


@pytest.fixture
def training_s3_uri(boto3_session, tempdir, bucket):
    s3_client = boto3_session.client('s3')
    filepath = os.path.join(tempdir, name())
    with open(filepath, 'w') as w:
        w.write('Hello World!')
    key = 'sagemaker/training-input/{}'.format(name())
    s3_client.upload_file(filepath, bucket, key)
    yield 's3://{}/{}'.format(bucket, key)
    s3_client.delete_object(Bucket=bucket, Key=key)


@pytest.fixture
def training_output_s3_uri(bucket):
    return 's3://{}/sagemaker/training-output/'.format(bucket)


@pytest.fixture
def training_job_name(sagemaker_boto_client, training_role_arn, docker_image,
                      training_s3_uri, training_output_s3_uri):
    training_job_name = name()
    sagemaker_boto_client.create_training_job(
        TrainingJobName=training_job_name,
        InputDataConfig=[
            {
                'ChannelName': 'train',
                'DataSource': {
                    'S3DataSource': {
                        'S3Uri': training_s3_uri,
                        'S3DataType': 'S3Prefix'
                    }
                }
            }
        ],
        AlgorithmSpecification={
            'TrainingImage': docker_image,
            'TrainingInputMode': 'File',
            'MetricDefinitions': [
                {

                    'Name': 'test-metric',
                    'Regex': 'test-metric = (.*)'

                }
            ],
            'EnableSageMakerMetricsTimeSeries': True
        },
        RoleArn=training_role_arn,
        ResourceConfig={
            'InstanceType': 'ml.m5.large',
            'InstanceCount': 1,
            'VolumeSizeInGB': 10
        },
        StoppingCondition={
            'MaxRuntimeInSeconds': 900
        },
        OutputDataConfig={
            'S3OutputPath': training_output_s3_uri
        },
        HyperParameters={
            '_enable_minerva_metrics': "true"
        },
    )
    return training_job_name


@pytest.fixture
def processing_job_name(sagemaker_boto_client, training_role_arn, docker_image):
    processing_job_name = name()
    sagemaker_boto_client.create_processing_job(
        ProcessingJobName=processing_job_name,
        ProcessingResources={
            'ClusterConfig': {
                'InstanceCount': 1,
                'InstanceType': 'ml.m5.large',
                'VolumeSizeInGB': 10
            }
        },
        AppSpecification={
            'ImageUri': docker_image
        },
        RoleArn=training_role_arn
    )
    return processing_job_name


@pytest.fixture(scope='session')
def docker_image():
    client = docker.from_env()
    ecr_client = boto3.client('ecr')
    token = ecr_client.get_authorization_token()
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    registry = token['authorizationData'][0]['proxyEndpoint']

    subprocess.check_call([sys.executable, 'setup.py', 'sdist'])
    [sdist_path] = glob.glob('dist/smexperiments*')
    shutil.copy(sdist_path, 'tests/integ-jobs/docker/smexperiments-0.1.0.tar.gz')

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
        buildargs={'library': 'smexperiments-0.1.0.tar.gz',
                   'botomodel': 'boto/sagemaker-experiments-2017-07-24.normal.json',
                   'script': 'scripts/script.py',
                   'endpoint': os.environ.get('SAGEMAKER_ENDPOINT', '')})
    client.images.push(tag, auth_config={'username': username, 'password': password})
    return tag
