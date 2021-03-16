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
import unittest.mock
import pytest
import shutil
import tempfile
import os
import datetime
from smexperiments import api_types, tracker, trial_component, _utils, _environment
import pandas as pd


@pytest.fixture
def boto3_session():
    mocked = unittest.mock.Mock()
    mocked.client.return_value.get_caller_identity.return_value = {"Account": unittest.mock.Mock()}
    return mocked


@pytest.fixture
def tempdir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)


@pytest.fixture
def metrics_dir(tempdir):
    saved = os.environ.get("SAGEMAKER_METRICS_DIRECTORY")
    os.environ["SAGEMAKER_METRICS_DIRECTORY"] = tempdir
    yield os.environ
    del os.environ["SAGEMAKER_METRICS_DIRECTORY"]
    if saved:
        os.environ["SAGEMAKER_METRICS_DIRECTORY"] = saved


@pytest.fixture
def sagemaker_boto_client(boto3_session):
    return boto3_session.client("sagemaker")


@pytest.fixture
def source_arn():
    return "source_arn"


@pytest.fixture
def environ(source_arn):
    contains = _utils.TRAINING_JOB_ARN_ENV in os.environ
    original_value = os.environ.get(_utils.TRAINING_JOB_ARN_ENV)
    os.environ[_utils.TRAINING_JOB_ARN_ENV] = source_arn
    yield
    if contains:
        os.environ[_utils.TRAINING_JOB_ARN_ENV] = original_value
    else:
        del os.environ[_utils.TRAINING_JOB_ARN_ENV]


@unittest.mock.patch("smexperiments._environment.TrialComponentEnvironment")
def test_load_in_sagemaker_training_job(mocked_tce, sagemaker_boto_client):
    trial_component_obj = trial_component.TrialComponent(
        trial_component_name="foo-bar", sagemaker_boto_client=sagemaker_boto_client
    )

    rv = unittest.mock.Mock()
    rv.source_arn = "arn:1234"
    rv.environment_type = _environment.EnvironmentType.SageMakerTrainingJob
    rv.get_trial_component.return_value = trial_component_obj
    mocked_tce.load.return_value = rv

    tracker_obj = tracker.Tracker.load(sagemaker_boto_client=sagemaker_boto_client)
    assert tracker_obj._in_sagemaker_job
    assert tracker_obj._metrics_writer
    assert tracker_obj.trial_component == trial_component_obj


@unittest.mock.patch("smexperiments._environment.TrialComponentEnvironment")
def test_load_in_sagemaker_processing_job(mocked_tce, sagemaker_boto_client):
    trial_component_obj = trial_component.TrialComponent(
        trial_component_name="foo-bar", sagemaker_boto_client=sagemaker_boto_client
    )

    rv = unittest.mock.Mock()
    rv.source_arn = "arn:1234"
    rv.environment_type = _environment.EnvironmentType.SageMakerProcessingJob
    rv.get_trial_component.return_value = trial_component_obj
    mocked_tce.load.return_value = rv

    tracker_obj = tracker.Tracker.load(sagemaker_boto_client=sagemaker_boto_client)
    assert tracker_obj._in_sagemaker_job
    assert tracker_obj._metrics_writer is None
    assert tracker_obj.trial_component == trial_component_obj


def test_load_in_sagemaker_job_no_resolved_tc(sagemaker_boto_client):
    with pytest.raises(ValueError):
        tracker.Tracker.load(sagemaker_boto_client=sagemaker_boto_client)


def test_load(boto3_session, sagemaker_boto_client):
    trial_component_name = "foo-trial-component"
    sagemaker_boto_client.describe_trial_component.return_value = {"TrialComponentName": trial_component_name}
    assert (
        trial_component_name
        == tracker.Tracker.load(
            trial_component_name=trial_component_name, sagemaker_boto_client=sagemaker_boto_client
        ).trial_component.trial_component_name
    )


def test_load_by_training_job_name(boto3_session, sagemaker_boto_client):
    training_job_name = "foo-training-job"
    trial_component_name = training_job_name + "-aws-training-job"
    sagemaker_boto_client.describe_trial_component.return_value = {"TrialComponentName": trial_component_name}
    assert (
        trial_component_name
        == tracker.Tracker.load(
            training_job_name=training_job_name, sagemaker_boto_client=sagemaker_boto_client
        ).trial_component.trial_component_name
    )


def test_load_by_processing_job_name(boto3_session, sagemaker_boto_client):
    processing_job_name = "foo-processing-job"
    trial_component_name = processing_job_name + "-aws-processing-job"
    sagemaker_boto_client.describe_trial_component.return_value = {"TrialComponentName": trial_component_name}
    assert (
        trial_component_name
        == tracker.Tracker.load(
            processing_job_name=processing_job_name, sagemaker_boto_client=sagemaker_boto_client
        ).trial_component.trial_component_name
    )


def test_create(boto3_session, sagemaker_boto_client):
    trial_component_name = "foo-trial-component"
    trial_component_display_name = "foo-trial-component-display-name"
    sagemaker_boto_client.create_trial_component.return_value = {"TrialComponentName": trial_component_name}
    tracker_created = tracker.Tracker.create(
        display_name=trial_component_display_name, sagemaker_boto_client=sagemaker_boto_client
    )
    assert trial_component_name == tracker_created.trial_component.trial_component_name

    assert tracker_created._metrics_writer is None


@pytest.fixture
def trial_component_obj(sagemaker_boto_client):
    return trial_component.TrialComponent(sagemaker_boto_client)


@pytest.fixture
def under_test(trial_component_obj):
    return tracker.Tracker(trial_component_obj, unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock())


def test_log_parameter(under_test):
    under_test.log_parameter("foo", "bar")
    assert under_test.trial_component.parameters["foo"] == "bar"
    under_test.log_parameter("whizz", 1)
    assert under_test.trial_component.parameters["whizz"] == 1


def test_enter(under_test):
    under_test.__enter__()
    assert isinstance(under_test.trial_component.start_time, datetime.datetime)
    assert under_test.trial_component.status.primary_status == "InProgress"


def test_cm(sagemaker_boto_client, under_test):
    sagemaker_boto_client.update_trial_component.return_value = {}
    with under_test:
        pass
    assert under_test.trial_component.status.primary_status == "Completed"
    assert isinstance(under_test.trial_component.end_time, datetime.datetime)


def test_cm_fail(sagemaker_boto_client, under_test):
    sagemaker_boto_client.update_trial_component.return_value = {}
    try:
        with under_test:
            raise ValueError("Foo")
    except ValueError:
        pass

    assert under_test.trial_component.status.primary_status == "Failed"
    assert under_test.trial_component.status.message
    assert isinstance(under_test.trial_component.end_time, datetime.datetime)


def test_enter_sagemaker_job(sagemaker_boto_client, under_test):
    sagemaker_boto_client.update_trial_component.return_value = {}
    under_test._in_sagemaker_job = True
    with under_test:
        pass
    assert under_test.trial_component.start_time is None
    assert under_test.trial_component.end_time is None
    assert under_test.trial_component.status is None


def test_log_parameters(under_test):
    under_test.log_parameters({"a": "b", "c": "d", "e": 5})
    assert under_test.trial_component.parameters == {"a": "b", "c": "d", "e": 5}


def test_log_input(under_test):
    under_test.log_input("foo", "baz", "text/text")
    assert under_test.trial_component.input_artifacts == {
        "foo": api_types.TrialComponentArtifact(value="baz", media_type="text/text")
    }


def test_log_output(under_test):
    under_test.log_output("foo", "baz", "text/text")
    assert under_test.trial_component.output_artifacts == {
        "foo": api_types.TrialComponentArtifact(value="baz", media_type="text/text")
    }


def test_log_metric(under_test):
    now = datetime.datetime.now()
    under_test.log_metric("foo", 1.0, 1, now)
    under_test._metrics_writer.log_metric.assert_called_with("foo", 1.0, 1, now)


def test_log_metric_attribute_error(under_test):
    now = datetime.datetime.now()

    exception = AttributeError

    under_test._metrics_writer.log_metric.side_effect = exception

    with pytest.raises(AttributeError):
        under_test.log_metric("foo", 1.0, 1, now)


def test_log_metric_attribute_error_warned(under_test):
    now = datetime.datetime.now()

    under_test._metrics_writer = None
    under_test._warned_on_metrics = None

    under_test.log_metric("foo", 1.0, 1, now)

    assert under_test._warned_on_metrics == True


def test_log_output_artifact(under_test):
    under_test._artifact_uploader.upload_artifact.return_value = ("s3uri_value", "etag_value")

    under_test.log_output_artifact("foo.txt", "name", "whizz/bang")
    under_test._artifact_uploader.upload_artifact.assert_called_with("foo.txt")
    assert "whizz/bang" == under_test.trial_component.output_artifacts["name"].media_type

    under_test.log_output_artifact("foo.txt")
    under_test._artifact_uploader.upload_artifact.assert_called_with("foo.txt")
    under_test._lineage_artifact_tracker.add_output_artifact.assert_called_with(
        "foo.txt", "s3uri_value", "etag_value", "text/plain"
    )
    assert "foo.txt" in under_test.trial_component.output_artifacts
    assert "text/plain" == under_test.trial_component.output_artifacts["foo.txt"].media_type


def test_log_input_artifact(under_test):
    under_test._artifact_uploader.upload_artifact.return_value = ("s3uri_value", "etag_value")

    under_test.log_input_artifact("foo.txt", "name", "whizz/bang")
    under_test._artifact_uploader.upload_artifact.assert_called_with("foo.txt")
    assert "whizz/bang" == under_test.trial_component.input_artifacts["name"].media_type

    under_test.log_input_artifact("foo.txt")
    under_test._artifact_uploader.upload_artifact.assert_called_with("foo.txt")
    under_test._lineage_artifact_tracker.add_input_artifact.assert_called_with(
        "foo.txt", "s3uri_value", "etag_value", "text/plain"
    )
    assert "foo.txt" in under_test.trial_component.input_artifacts
    assert "text/plain" == under_test.trial_component.input_artifacts["foo.txt"].media_type


def test_log_inputs_error(under_test):
    for index in range(0, 30):
        file_path = "foo" + str(index) + ".txt"
        under_test.trial_component.input_artifacts[file_path] = {
            "foo": api_types.TrialComponentArtifact(value="baz" + str(index), media_type="text/text")
        }
    with pytest.raises(ValueError):
        under_test.log_input("foo.txt", "name", "whizz/bang")


def test_log_outputs(under_test):
    for index in range(0, 30):
        file_path = "foo" + str(index) + ".txt"
        under_test.trial_component.output_artifacts[file_path] = {
            "foo": api_types.TrialComponentArtifact(value="baz" + str(index), media_type="text/text")
        }
    with pytest.raises(ValueError):
        under_test.log_output("foo.txt", "name", "whizz/bang")


def test_log_multiple_input_artifact(under_test):
    for index in range(0, 30):
        file_path = "foo" + str(index) + ".txt"
        under_test._artifact_uploader.upload_artifact.return_value = (
            "s3uri_value" + str(index),
            "etag_value" + str(index),
        )
        under_test.log_input_artifact(file_path, "name" + str(index), "whizz/bang" + str(index))
        under_test._artifact_uploader.upload_artifact.assert_called_with(file_path)

    under_test._artifact_uploader.upload_artifact.return_value = ("s3uri_value", "etag_value")
    with pytest.raises(ValueError):
        under_test.log_input_artifact("foo.txt", "name", "whizz/bang")


def test_log_multiple_output_artifact(under_test):
    for index in range(0, 30):
        file_path = "foo" + str(index) + ".txt"
        under_test._artifact_uploader.upload_artifact.return_value = (
            "s3uri_value" + str(index),
            "etag_value" + str(index),
        )
        under_test.log_output_artifact(file_path, "name" + str(index), "whizz/bang" + str(index))
        under_test._artifact_uploader.upload_artifact.assert_called_with(file_path)

    under_test._artifact_uploader.upload_artifact.return_value = ("s3uri_value", "etag_value")
    with pytest.raises(ValueError):
        under_test.log_output_artifact("foo.txt", "name", "whizz/bang")


def test_log_pr_curve(under_test):

    y_true = [0, 0, 1, 1]
    y_scores = [0.1, 0.4, 0.35, 0.8]
    no_skill = 0.1

    under_test._artifact_uploader.upload_object_artifact.return_value = ("s3uri_value", "etag_value")

    under_test.log_precision_recall(y_true, y_scores, title="TestPRCurve", no_skill=no_skill)

    expected_data = {
        "type": "PrecisionRecallCurve",
        "version": 0,
        "title": "TestPRCurve",
        "precision": [0.6666666666666666, 0.5, 1.0, 1.0],
        "recall": [1.0, 0.5, 0.5, 0.0],
        "averagePrecisionScore": 0.8333333333333333,
        "noSkill": 0.1,
    }
    under_test._artifact_uploader.upload_object_artifact.assert_called_with(
        "TestPRCurve", expected_data, file_extension="json"
    )

    under_test._lineage_artifact_tracker.add_input_artifact(
        "TestPRCurve", "s3uri_value", "etag_value", "PrecisionRecallCurve"
    )


def test_log_confusion_matrix(under_test):

    y_true = [2, 0, 2, 2, 0, 1]
    y_pred = [0, 0, 2, 2, 0, 2]

    under_test._artifact_uploader.upload_object_artifact.return_value = ("s3uri_value", "etag_value")

    under_test.log_confusion_matrix(y_true, y_pred, title="TestConfusionMatrix")

    expected_data = {
        "type": "ConfusionMatrix",
        "version": 0,
        "title": "TestConfusionMatrix",
        "confusionMatrix": [[2, 0, 0], [0, 0, 1], [1, 0, 2]],
    }

    under_test._artifact_uploader.upload_object_artifact.assert_called_with(
        "TestConfusionMatrix", expected_data, file_extension="json"
    )

    under_test._lineage_artifact_tracker.add_input_artifact(
        "TestConfusionMatrix", "s3uri_value", "etag_value", "ConfusionMatrix"
    )


def test_resolve_artifact_name():
    file_names = {
        "a": "a",
        "a.txt": "a.txt",
        "b.": "b.",
        ".c": ".c",
        "/x/a/a.txt": "a.txt",
        "/a/b/c.": "c.",
        "./.a": ".a",
        "../b.txt": "b.txt",
        "~/a.txt": "a.txt",
        "c/d.txt": "d.txt",
    }
    for file_name, artifact_name in file_names.items():
        assert artifact_name == tracker._resolve_artifact_name(file_name)


@pytest.fixture
def artifact_uploader(boto3_session):
    return tracker._ArtifactUploader("trial_component_name", "artifact_bucket", "artifact_prefix", boto3_session)


def test_artifact_uploader_init(artifact_uploader):
    assert "trial_component_name" == artifact_uploader.trial_component_name
    assert "artifact_bucket" == artifact_uploader.artifact_bucket
    assert "artifact_prefix" == artifact_uploader.artifact_prefix


def test_artifact_uploader_upload_artifact_file_not_exists(tempdir, artifact_uploader):

    not_exist_file = os.path.join(tempdir, "not.exists")
    with pytest.raises(ValueError):
        artifact_uploader.upload_artifact(not_exist_file)


def test_artifact_uploader_s3(tempdir, artifact_uploader):
    path = os.path.join(tempdir, "exists")
    with open(path, "a") as f:
        f.write("boo")

    name = tracker._resolve_artifact_name(path)
    artifact_uploader.s3_client.head_object.return_value = {"ETag": "etag_value"}

    s3_uri, etag = artifact_uploader.upload_artifact(path)
    expected_key = "{}/{}/{}".format(artifact_uploader.artifact_prefix, artifact_uploader.trial_component_name, name)

    artifact_uploader.s3_client.upload_file.assert_called_with(path, artifact_uploader.artifact_bucket, expected_key)

    expected_uri = "s3://{}/{}".format(artifact_uploader.artifact_bucket, expected_key)
    assert expected_uri == s3_uri


def test_guess_media_type():
    assert "text/plain" == tracker._guess_media_type("foo.txt")


@pytest.fixture
def lineage_artifact_tracker(sagemaker_boto_client):
    return tracker._LineageArtifactTracker("test_trial_component_arn", sagemaker_boto_client)


def test_lineage_artifact_tracker(lineage_artifact_tracker, sagemaker_boto_client):
    lineage_artifact_tracker.add_input_artifact("input_name", "input_source_uri", "input_etag", "text/plain")
    lineage_artifact_tracker.add_output_artifact("output_name", "output_source_uri", "output_etag", "text/plain")
    sagemaker_boto_client.create_artifact.side_effect = [
        {"ArtifactArn": "created_arn_1"},
        {"ArtifactArn": "created_arn_2"},
    ]

    lineage_artifact_tracker.save()

    expected_calls = [
        unittest.mock.call(
            ArtifactName="input_name",
            ArtifactType="text/plain",
            Source={
                "SourceUri": "input_source_uri",
                "SourceTypes": [{"SourceIdType": "S3ETag", "Value": "input_etag"}],
            },
        ),
        unittest.mock.call(
            ArtifactName="output_name",
            ArtifactType="text/plain",
            Source={
                "SourceUri": "output_source_uri",
                "SourceTypes": [{"SourceIdType": "S3ETag", "Value": "output_etag"}],
            },
        ),
    ]
    assert expected_calls == sagemaker_boto_client.create_artifact.mock_calls

    expected_calls = [
        unittest.mock.call(
            SourceArn="created_arn_1", DestinationArn="test_trial_component_arn", AssociationType="ContributedTo"
        ),
        unittest.mock.call(
            SourceArn="test_trial_component_arn", DestinationArn="created_arn_2", AssociationType="Produced"
        ),
    ]
    assert expected_calls == sagemaker_boto_client.add_association.mock_calls


def test_convert_dict_to_fields():
    values = {"x": [1, 2, 3], "y": [4, 5, 6]}
    fields = tracker._ArtifactConverter.convert_dict_to_fields(values)

    expected_fields = [
        {"name": "x", "type": "string"},
        {"name": "y", "type": "string"},
    ]

    assert expected_fields == fields


def test_convert_data_frame_to_values():
    df = pd.DataFrame({"col1": [1, 2], "col2": [0.5, 0.75]})

    values = tracker._ArtifactConverter.convert_data_frame_to_values(df)

    expected_values = {"col1": [1, 2], "col2": [0.5, 0.75]}

    assert expected_values == values


def test_convert_data_frame_to_fields():
    df = pd.DataFrame({"col1": [1, 2], "col2": [0.5, 0.75]})

    fields = tracker._ArtifactConverter.convert_data_frame_to_fields(df)

    expected_fields = [{"name": "col1", "type": "number"}, {"name": "col2", "type": "number"}]

    assert expected_fields == fields


def test_convert_df_type_to_simple_type():
    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("float64")
    assert actual == "number"

    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("int32")
    assert actual == "number"

    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("uint32")
    assert actual == "number"

    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("datetime64")
    assert actual == "datetime"

    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("boolean")
    assert actual == "boolean"

    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("category")
    assert actual == "string"

    actual = tracker._ArtifactConverter.convert_df_type_to_simple_type("sometype")
    assert actual == "string"


def test_log_table_both_specified(under_test):
    with pytest.raises(ValueError):
        under_test.log_table(title="test", values={"foo": "bar"}, data_frame={"foo": "bar"})


def test_log_table_neither_specified(under_test):
    with pytest.raises(ValueError):
        under_test.log_table(title="test")


def test_log_table_invalid_values(under_test):
    values = {"x": "foo", "y": [4, 5, 6]}

    with pytest.raises(ValueError):
        under_test.log_table(title="test", values=values)


def test_log_table(under_test):

    values = {"x": [1, 2, 3], "y": [4, 5, 6]}

    under_test._artifact_uploader.upload_object_artifact.return_value = ("s3uri_value", "etag_value")

    under_test.log_table(title="TestTable", values=values)
    expected_data = {
        "type": "Table",
        "version": 0,
        "title": "TestTable",
        "fields": [
            {"name": "x", "type": "string"},
            {"name": "y", "type": "string"},
        ],
        "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
    }
    under_test._artifact_uploader.upload_object_artifact.assert_called_with(
        "TestTable", expected_data, file_extension="json"
    )

    under_test._lineage_artifact_tracker.add_input_artifact("TestTable", "s3uri_value", "etag_value", "Table")


def test_log_roc_curve(under_test):
    y_true = [0, 0, 1, 1]
    y_scores = [0.1, 0.4, 0.35, 0.8]

    under_test._artifact_uploader.upload_object_artifact.return_value = ("s3uri_value", "etag_value")

    under_test.log_roc_curve(y_true, y_scores, title="TestROCCurve")

    expected_data = {
        "type": "ROCCurve",
        "version": 0,
        "title": "TestROCCurve",
        "falsePositiveRate": [0.0, 0.0, 0.5, 0.5, 1.0],
        "truePositiveRate": [0.0, 0.5, 0.5, 1.0, 1.0],
        "areaUnderCurve": 0.75,
    }
    under_test._artifact_uploader.upload_object_artifact.assert_called_with(
        "TestROCCurve", expected_data, file_extension="json"
    )

    under_test._lineage_artifact_tracker.add_input_artifact("TestROCCurve", "s3uri_value", "etag_value", "ROCCurve")
