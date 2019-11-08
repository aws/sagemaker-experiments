import pytest
import uuid
import boto3
import tempfile
import shutil
import os
import time
import logging


from smexperiments import experiment, trial, trial_component


@pytest.fixture
def sagemaker_boto_client():
    if 'SAGEMAKER_ENDPOINT' in os.environ:
        return boto3.client('sagemaker', endpoint_url=os.environ.get('SAGEMAKER_ENDPOINT'))
    else:
        return boto3.client('sagemaker')

@pytest.fixture(scope='session')
def boto3_session():
    return boto3.Session(region_name='us-west-2')


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
    bucket_name = 'sagemaker-experiments-integ-test'
    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration = {
                'LocationConstraint': 'us-west-2'
            }
        )
    except Exception as ex:
        if 'BucketAlreadyOwnedByYou' in str(ex):
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
def training_job_name(sagemaker_boto_client, training_role_arn, training_docker_image,
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
            'TrainingImage': training_docker_image,
            'TrainingInputMode': 'File',
            'MetricDefinitions': [
                {

                    'Name': 'test-metric',
                    'Regex': 'test-metric = (.*)'

                }
            ]
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
