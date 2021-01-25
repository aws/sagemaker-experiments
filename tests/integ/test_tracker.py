# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import os
import logging

import pytest

from tests.helpers import name, wait_for_trial_component
from smexperiments import tracker, trial_component, _utils


def test_load_trial_component(trial_component_obj, sagemaker_boto_client):
    wait_for_trial_component(sagemaker_boto_client, trial_component_name=trial_component_obj.trial_component_name)
    tracker_obj = tracker.Tracker.load(
        trial_component_name=trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
    )
    assert tracker_obj
    assert tracker_obj.trial_component.trial_component_name == trial_component_obj.trial_component_name


@pytest.mark.docker
def test_load_training_job(training_job_name, sagemaker_boto_client):
    wait_for_trial_component(sagemaker_boto_client, training_job_name=training_job_name)
    tracker_obj = tracker.Tracker.load(training_job_name=training_job_name, sagemaker_boto_client=sagemaker_boto_client)
    assert tracker_obj
    assert tracker_obj.trial_component.trial_component_name == training_job_name + "-aws-training-job"


def test_load_trial_component_fails(sagemaker_boto_client):
    with pytest.raises(ValueError):
        tracker.Tracker.load(sagemaker_boto_client=sagemaker_boto_client)


def test_create(sagemaker_boto_client):
    tracker_obj = tracker.Tracker.create(sagemaker_boto_client=sagemaker_boto_client)
    try:
        sagemaker_boto_client.describe_trial_component(
            TrialComponentName=tracker_obj.trial_component.trial_component_name
        )
    finally:
        tracker_obj.trial_component.delete()


def test_create_display_name(sagemaker_boto_client):
    display_name = name()
    tracker_obj = tracker.Tracker.create(display_name=display_name, sagemaker_boto_client=sagemaker_boto_client)
    try:
        assert display_name == tracker_obj.trial_component.display_name
    finally:
        tracker_obj.trial_component.delete()


def test_log_simple(trial_component_obj, sagemaker_boto_client):
    with tracker.Tracker.load(
        trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
    ) as tracker_obj:
        tracker_obj.log_parameter("p1", 1.0)
        tracker_obj.log_parameter("p2", "p2-value")
        tracker_obj.log_parameters({"p3": 2.0, "p4": "p4-value"})
    loaded_obj = trial_component.TrialComponent.load(
        trial_component_name=trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
    )
    expected_parameters = {"p1": 1.0, "p2": "p2-value", "p3": 2.0, "p4": "p4-value"}
    assert expected_parameters == loaded_obj.parameters


def test_log_artifact(trial_component_obj, bucket, tempdir, sagemaker_boto_client):
    prefix = name()
    file_contents = "happy monkey monkey"
    file_path = os.path.join(tempdir, "foo.txt")
    artifact_name = "monkey-monkey"
    with open(file_path, "w") as foo_file:
        foo_file.write(file_contents)

    with tracker.Tracker.load(
        trial_component_obj.trial_component_name,
        artifact_bucket=bucket,
        artifact_prefix=prefix,
        sagemaker_boto_client=sagemaker_boto_client,
    ) as tracker_obj:
        tracker_obj.log_artifact(file_path, name=artifact_name)

    loaded = trial_component.TrialComponent.load(
        trial_component_name=trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
    )
    assert "text/plain" == loaded.output_artifacts[artifact_name].media_type
    assert prefix in loaded.output_artifacts[artifact_name].value


def test_log_artifacts(trial_component_obj, bucket, tempdir, sagemaker_boto_client):
    prefix = name()
    file_contents = "happy monkey monkey"
    file_path = os.path.join(tempdir, "foo.txt")
    file_path1 = os.path.join(tempdir, "bar.txt")
    with open(file_path, "w") as foo_file:
        foo_file.write(file_contents)
    with open(file_path1, "w") as bar_file:
        bar_file.write(file_contents)

    with tracker.Tracker.load(
        trial_component_obj.trial_component_name,
        artifact_bucket=bucket,
        artifact_prefix=prefix,
        sagemaker_boto_client=sagemaker_boto_client,
    ) as tracker_obj:
        tracker_obj.log_artifacts(tempdir)
    loaded = trial_component.TrialComponent.load(
        trial_component_name=trial_component_obj.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
    )
    assert "text/plain" == loaded.output_artifacts["foo"].media_type
    assert prefix in loaded.output_artifacts["foo"].value
    assert "text/plain" == loaded.output_artifacts["bar"].media_type
    assert prefix in loaded.output_artifacts["bar"].value


def test_create_default_bucket(boto3_session):
    bucket_name_prefix = _utils.name("sm-test")
    bucket = _utils.get_or_create_default_bucket(boto3_session, default_bucket_prefix=bucket_name_prefix)
    s3_client = boto3_session.client("s3")
    try:
        s3_client.head_bucket(Bucket=bucket)
    finally:
        s3_client.delete_bucket(Bucket=bucket)


def test_create_lineage_artifacts(trial_component_obj, bucket, tempdir, sagemaker_boto_client):

    prefix = name()
    file_contents = "test lineage artifact"
    file_path = os.path.join(tempdir, "bar.txt")
    artifact_name = "goonies"

    with open(file_path, "w") as foo_file:
        foo_file.write(file_contents)

    with tracker.Tracker.load(
        trial_component_obj.trial_component_name,
        artifact_bucket=bucket,
        artifact_prefix=prefix,
        sagemaker_boto_client=sagemaker_boto_client,
    ) as tracker_obj:
        tracker_obj.log_output_artifact(file_path, name=artifact_name)

    response = sagemaker_boto_client.list_associations(SourceArn=trial_component_obj.trial_component_arn)
    associations = response["AssociationSummaries"]
    assert len(associations) == 1
    summary = associations[0]
    logging.info(summary)
    assert summary["SourceArn"] == trial_component_obj.trial_component_arn
    assert summary["DestinationName"] == artifact_name


def test_log_table_artifact(trial_component_obj, bucket, sagemaker_boto_client):

    prefix = name()
    artifact_name = "TestTableTitle"

    values = {"x": [1, 2, 3], "y": [4, 5, 6]}

    with tracker.Tracker.load(
        trial_component_obj.trial_component_name,
        artifact_bucket=bucket,
        artifact_prefix=prefix,
        sagemaker_boto_client=sagemaker_boto_client,
    ) as tracker_obj:
        tracker_obj.log_table(title=artifact_name, values=values)

    response = sagemaker_boto_client.list_associations(SourceArn=trial_component_obj.trial_component_arn)
    associations = response["AssociationSummaries"]
    assert len(associations) == 1
    summary = associations[0]
    logging.info(summary)
    assert summary["SourceArn"] == trial_component_obj.trial_component_arn
    assert summary["DestinationName"] == artifact_name
