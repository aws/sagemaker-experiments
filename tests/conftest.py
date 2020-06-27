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
from tests.helpers import name, names


def pytest_addoption(parser):
    parser.addoption("--boto-model-file", action="store", default=None)
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")
    parser.addoption("--sagemaker-endpoint", action="store", default=None)
    parser.addoption("--region", action="store", default="us-west-2")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def boto_model_file(request):
    return request.config.getoption("--boto-model-file")


@pytest.fixture(scope="session")
def sagemaker_endpoint(request):
    return request.config.getoption("--sagemaker-endpoint")


@pytest.fixture(scope="session")
def sagemaker_region(request):
    return request.config.getoption("--region")


@pytest.fixture
def sagemaker_boto_client(sagemaker_endpoint, sagemaker_region):
    if sagemaker_endpoint is None:
        return boto3.client("sagemaker", region_name=sagemaker_region)
    else:
        return boto3.client("sagemaker", region_name=sagemaker_region, endpoint_url=sagemaker_endpoint)


@pytest.fixture(scope="session")
def boto3_session():
    return boto3.Session()


@pytest.fixture
def tempdir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def experiment_obj(sagemaker_boto_client):
    description = "{}-{}".format("description", str(uuid.uuid4()))
    boto3.set_stream_logger("", logging.INFO)
    experiment_obj = experiment.Experiment.create(
        experiment_name=name(), description=description, sagemaker_boto_client=sagemaker_boto_client
    )
    yield experiment_obj
    time.sleep(0.5)
    experiment_obj.delete()


@pytest.fixture
def trial_obj(sagemaker_boto_client, experiment_obj):
    trial_obj = trial.Trial.create(
        trial_name=name(), experiment_name=experiment_obj.experiment_name, sagemaker_boto_client=sagemaker_boto_client
    )
    yield trial_obj
    time.sleep(0.5)
    trial_obj.delete()


@pytest.fixture
def trial_component_obj(sagemaker_boto_client):
    trial_component_obj = trial_component.TrialComponent.create(
        trial_component_name=name(), sagemaker_boto_client=sagemaker_boto_client
    )
    yield trial_component_obj
    time.sleep(0.5)
    trial_component_obj.delete()


@pytest.fixture
def trial_component_with_disassociation_obj(trials, sagemaker_boto_client):
    trial_component_obj = trial_component.TrialComponent.create(
        trial_component_name=name(), sagemaker_boto_client=sagemaker_boto_client
    )
    for trial in trials:
        sagemaker_boto_client.associate_trial_component(
            TrialName=trial.trial_name, TrialComponentName=trial_component_obj.trial_component_name
        )
        # print(trials).trial_name
    yield trial_component_obj
    time.sleep(0.5)
    trial_component_obj.delete(disassociate=True)


@pytest.fixture
def trials(experiment_obj, sagemaker_boto_client):
    trial_objs = []
    for trial_name in names():
        next_trial = trial.Trial.create(
            trial_name=trial_name,
            experiment_name=experiment_obj.experiment_name,
            sagemaker_boto_client=sagemaker_boto_client,
        )
        trial_objs.append(next_trial)
        time.sleep(0.5)
    yield trial_objs
    for trial_obj in trial_objs:
        trial_obj.delete()


@pytest.fixture
def experiments(sagemaker_boto_client):
    experiment_objs = []

    for experiment_name in names():
        experiment_objs.append(
            experiment.Experiment.create(experiment_name=experiment_name, sagemaker_boto_client=sagemaker_boto_client)
        )
        time.sleep(1)

    yield experiment_objs
    for experiment_obj in experiment_objs:
        experiment_obj.delete()


@pytest.fixture
def trial_components(sagemaker_boto_client):
    trial_component_objs = [
        trial_component.TrialComponent.create(
            trial_component_name=trial_component_name, sagemaker_boto_client=sagemaker_boto_client
        )
        for trial_component_name in names()
    ]
    yield trial_component_objs
    for trial_component_obj in trial_component_objs:
        trial_component_obj.delete()


@pytest.fixture
def trial_components_in_trial(sagemaker_boto_client, trial_obj):
    trial_components = [
        trial_component.TrialComponent.create(
            trial_component_name=trial_component_name, sagemaker_boto_client=sagemaker_boto_client
        )
        for trial_component_name in names()
    ]
    for trial_component_obj in trial_components:
        trial_obj.add_trial_component(trial_component_obj)
    yield trial_components
    for trial_component_obj in trial_components:
        trial_obj.remove_trial_component(trial_component_obj)
        trial_component_obj.delete()


@pytest.fixture(scope="session")
def training_role_arn(boto3_session):
    iam_client = boto3_session.client("iam")
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
    policy_string = "".join(policy_string.split())  # strip all whitespace
    role_name = "SMExperimentsIntegTestSageMakerRole"
    try:
        response = iam_client.create_role(RoleName=role_name, AssumeRolePolicyDocument=policy_string)
    except Exception as ex:
        if "exists" in str(ex):
            return iam_client.get_role(RoleName=role_name)["Role"]["Arn"]
        else:
            raise ex

    iam_client.attach_role_policy(RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess")
    time.sleep(30)
    return response["Role"]["Arn"]


@pytest.fixture(scope="session")
def bucket(boto3_session):
    s3_client = boto3_session.client("s3")
    sts_client = boto3_session.client("sts")
    account = sts_client.get_caller_identity()["Account"]

    bucket_name = "sagemaker-experiments-integ-test-%s-%s" % (boto3_session.region_name, account)
    try:
        if boto3_session.region_name != "us-east-1":
            s3_client.create_bucket(
                Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": boto3_session.region_name}
            )
        else:
            s3_client.create_bucket(Bucket=bucket_name)
    except Exception as ex:
        if "BucketAlreadyOwnedByYou" in str(ex) or "BucketAlreadyExists" in str(ex):
            return bucket_name
        raise ex
    return bucket_name


@pytest.fixture
def training_s3_uri(boto3_session, tempdir, bucket):
    s3_client = boto3_session.client("s3")
    filepath = os.path.join(tempdir, name())
    with open(filepath, "w") as w:
        w.write("Hello World!")
    key = "sagemaker/training-input/{}".format(name())
    s3_client.upload_file(filepath, bucket, key)
    yield "s3://{}/{}".format(bucket, key)
    s3_client.delete_object(Bucket=bucket, Key=key)


@pytest.fixture
def training_output_s3_uri(bucket):
    return "s3://{}/sagemaker/training-output/".format(bucket)


@pytest.fixture
def training_job_name(sagemaker_boto_client, training_role_arn, docker_image, training_s3_uri, training_output_s3_uri):
    training_job_name = name()
    sagemaker_boto_client.create_training_job(
        TrainingJobName=training_job_name,
        InputDataConfig=[
            {
                "ChannelName": "train",
                "DataSource": {"S3DataSource": {"S3Uri": training_s3_uri, "S3DataType": "S3Prefix"}},
            }
        ],
        AlgorithmSpecification={"TrainingImage": docker_image, "TrainingInputMode": "File",},
        RoleArn=training_role_arn,
        ResourceConfig={"InstanceType": "ml.m5.large", "InstanceCount": 1, "VolumeSizeInGB": 10},
        StoppingCondition={"MaxRuntimeInSeconds": 900},
        OutputDataConfig={"S3OutputPath": training_output_s3_uri},
    )
    return training_job_name


@pytest.fixture
def processing_job_name(sagemaker_boto_client, training_role_arn, docker_image):
    processing_job_name = name()
    sagemaker_boto_client.create_processing_job(
        ProcessingJobName=processing_job_name,
        ProcessingResources={
            "ClusterConfig": {"InstanceCount": 1, "InstanceType": "ml.m5.large", "VolumeSizeInGB": 10}
        },
        AppSpecification={"ImageUri": docker_image},
        RoleArn=training_role_arn,
    )
    return processing_job_name


@pytest.fixture(scope="session")
def docker_image(boto_model_file, sagemaker_endpoint):
    client = docker.from_env()
    ecr_client = boto3.client("ecr")
    token = ecr_client.get_authorization_token()
    username, password = base64.b64decode(token["authorizationData"][0]["authorizationToken"]).decode().split(":")
    registry = token["authorizationData"][0]["proxyEndpoint"]
    repository_name = "smexperiments-test"
    image_version = "1.0.0"
    tag = "{}/{}:{}".format(registry, repository_name, image_version)[8:]

    # initialize the docker image repository
    try:
        ecr_client.create_repository(repositoryName=repository_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryAlreadyExistsException":
            pass
        else:
            raise

    # pull existing image for layer cache
    try:
        client.images.pull(tag, auth_config={"username": username, "password": password})
        print("Docker image with tag {} already exists.".format(tag))
        # the image with this tag already exists
        return tag
    except docker.errors.NotFound:
        pass

    if boto_model_file is None:
        print("boto_model_file is None, using default model.")
    else:
        shutil.copy(boto_model_file, "tests/integ-jobs/docker/boto/sagemaker-experiments-2017-07-24.normal.json")

    subprocess.check_call([sys.executable, "setup.py", "sdist"])
    [sdist_path] = glob.glob("dist/sagemaker-experiments*")
    shutil.copy(sdist_path, "tests/integ-jobs/docker/smexperiments-0.1.0.tar.gz")

    os.makedirs("tests/integ-jobs/docker/boto", exist_ok=True)

    client.images.build(
        path="tests/integ-jobs/docker",
        dockerfile="Dockerfile",
        tag=tag,
        cache_from=[tag],
        buildargs={
            "library": "smexperiments-0.1.0.tar.gz",
            "botomodel": "boto/sagemaker-experiments-2017-07-24.normal.json",
            "script": "scripts/script.py",
            "endpoint": sagemaker_endpoint,
        },
    )
    client.images.push(tag, auth_config={"username": username, "password": password})
    return tag
