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
"""Contains the SageMaker Experiments Tracker class."""
import datetime
import os
import mimetypes
import urllib.parse
import urllib.request
import logging
import botocore
import json
from smexperiments._utils import get_module
from os.path import join

import dateutil

from smexperiments import api_types, metrics, trial_component, _utils, _environment


class Tracker(object):
    """A SageMaker Experiments Tracker.

    Use a tracker object to record experiment information to a SageMaker trial component.

    A new tracker can be created in two ways:

    - By loading an existing trial component with :meth:`~smexperiments.tracker.Tracker.load`
    - By creating a tracker for a new trial component with :meth:`~smexperiments.tracker.Tracker.create`.

    When creating a tracker within a SageMaker training or processing job, use the ``load`` method with
    no arguments to track artifacts to the trial component automatically created for your job. When tracking
    within a Jupyter notebook running in SageMaker, use the ``create`` method to automatically
    create a new
    trial component.

    Trackers are Python context managers and you can use them using the Python ``with`` keyword. Exceptions
    thrown within the with block will cause the tracker's trial component to be marked as failed. Start and
    end times are automatically set when using the with statement and the trial component is saved to
    SageMaker at the end of the block.

    Note that only parameters, input artifacts, and output artifacts are saved to SageMaker. Metrics are saved to file.

    Attributes:
        trial_component (TrialComponent): The trial component tracked.
    """

    trial_component = None
    _metrics_writer = None
    _in_sagemaker_job = False
    _artifact_uploader = None

    def __init__(self, trial_component, metrics_writer, artifact_uploader, lineage_artifact_tracker):
        self.trial_component = trial_component
        self.trial_component.parameters = self.trial_component.parameters or {}
        self.trial_component.input_artifacts = self.trial_component.input_artifacts or {}
        self.trial_component.output_artifacts = self.trial_component.output_artifacts or {}
        self._artifact_uploader = artifact_uploader
        self._metrics_writer = metrics_writer
        self._warned_on_metrics = False
        self._lineage_artifact_tracker = lineage_artifact_tracker

    @classmethod
    def load(
        cls,
        trial_component_name=None,
        artifact_bucket=None,
        artifact_prefix=None,
        boto3_session=None,
        sagemaker_boto_client=None,
        training_job_name=None,
        processing_job_name=None,
    ):
        """Create a new ``Tracker`` by loading an existing trial component.

        Examples:
            .. code-block:: python

                from smexperiments import tracker

                # load tracker from already existing trial component
                my_tracker = tracker.Tracker.load(trial_component_name='xgboost')

                # load tracker from a training job name
                my_tracker = tracker.Tracker.load(
                    training_job_name=estimator.latest_training_job.name)

                # load tracker from a processing job name
                my_tracker = tracker.Tracker.load(
                    processing_job_name=my_processing_job.name)

        Args:
            trial_component_name: (str, optional). The name of the trial component to track. If specified, this
                trial component must exist in SageMaker. If you invoke this method in a running SageMaker training
                or processing job, then trial_component_name can be left empty. In this case, the Tracker will
                resolve the trial component automatically created for your SageMaker Job.
            artifact_bucket: (str, optional) The name of the S3 bucket to store artifacts to.
            artifact_prefix: (str, optional) The prefix to write artifacts to within ``artifact_bucket``
            boto3_session: (boto3.Session, optional) The boto3.Session to use to interact with AWS services.
                If not specified a new default boto3 session will be created.
            sagemaker_boto_client: (boto3.Client, optional) The SageMaker AWS service client to use. If not
                specified a new client will be created from the specified ``boto3_session`` or default
                boto3.Session.
            training_job_name: (str, optional). The name of the training job to track via trial
            processing_job_name: (str, optional). The name of the processing job to track via trial
                component.

        Returns:
            Tracker: The tracker for the given trial component.

        Raises:
            ValueError: If the trial component failed to load.
        """
        boto3_session = boto3_session or _utils.boto_session()
        sagemaker_boto_client = sagemaker_boto_client or _utils.sagemaker_client()

        tce = _environment.TrialComponentEnvironment.load()

        if training_job_name and not trial_component_name:
            trial_component_name = training_job_name + "-aws-training-job"
        elif processing_job_name and not trial_component_name:
            trial_component_name = processing_job_name + "-aws-processing-job"

        # Resolve the trial component for this tracker to track: If a trial component name was passed in, then load
        # and track that trial component. Otherwise, try to find a trial component given the current environment,
        # failing if we're unable to load one.
        if trial_component_name:
            tc = trial_component.TrialComponent.load(
                trial_component_name=trial_component_name, sagemaker_boto_client=sagemaker_boto_client
            )
        elif tce:
            tc = tce.get_trial_component(sagemaker_boto_client)
        else:
            raise ValueError('Could not load TrialComponent. Specify a trial_component_name or invoke "create"')

        # if running in a SageMaker context write metrics to file
        if not trial_component_name and tce.environment_type == _environment.EnvironmentType.SageMakerTrainingJob:
            metrics_writer = metrics.SageMakerFileMetricsWriter()
        else:
            metrics_writer = None

        tracker = cls(
            tc,
            metrics_writer,
            _ArtifactUploader(tc.trial_component_name, artifact_bucket, artifact_prefix, boto3_session),
            _LineageArtifactTracker(tc.trial_component_arn, sagemaker_boto_client),
        )
        tracker._in_sagemaker_job = True if tce else False
        return tracker

    @classmethod
    def create(
        cls,
        display_name=None,
        artifact_bucket=None,
        artifact_prefix=None,
        boto3_session=None,
        sagemaker_boto_client=None,
    ):
        """Create a new ``Tracker`` by creating a new trial component.

        Examples
            .. code-block:: python

                from smexperiments import tracker

                my_tracker = tracker.Tracker.create()

        Args:
            display_name: (str, optional). The display name of the trial component to track.
            artifact_bucket: (str, optional) The name of the S3 bucket to store artifacts to.
            artifact_prefix: (str, optional) The prefix to write artifacts to within ``artifact_bucket``
            boto3_session: (boto3.Session, optional) The boto3.Session to use to interact with AWS services.
                If not specified a new default boto3 session will be created.
            sagemaker_boto_client: (boto3.Client, optional) The SageMaker AWS service client to use. If not
                specified a new client will be created from the specified ``boto3_session`` or default
                boto3.Session.

        Returns:
            Tracker: The tracker for the new trial component.
        """
        boto3_session = boto3_session or _utils.boto_session()
        sagemaker_boto_client = sagemaker_boto_client or _utils.sagemaker_client()

        tc = trial_component.TrialComponent.create(
            trial_component_name=_utils.name("TrialComponent"),
            display_name=display_name,
            sagemaker_boto_client=sagemaker_boto_client,
        )

        metrics_writer = metrics.SageMakerFileMetricsWriter()

        return cls(
            tc,
            metrics_writer,
            _ArtifactUploader(tc.trial_component_name, artifact_bucket, artifact_prefix, boto3_session),
            _LineageArtifactTracker(tc.trial_component_arn, sagemaker_boto_client),
        )

    def log_parameter(self, name, value):
        """Record a single parameter value for this trial component.

        Overwrites any previous value recorded for the specified parameter name.

        Examples
            .. code-block:: python

                # log hyper parameter of learning rate
                my_tracker.log_parameter('learning_rate', 0.01)

        Args:
            name (str): The name of the parameter
            value (str or numbers.Number): The value of the parameter
        """
        self.trial_component.parameters[name] = value

    def log_parameters(self, parameters):
        """Record a collection of parameter values for this trial component.

        Examples
            .. code-block:: python

                # log multiple hyper parameters used in training
                my_tracker.log_parameters({"learning_rate": 1.0, "gamma": 0.9, "dropout": 0.5})

        Args:
            parameters (dict[str, str or numbers.Number]): The parameters to record.
        """
        self.trial_component.parameters.update(parameters)

    def log_input(self, name, value, media_type=None):
        """Record a single input artifact for this trial component.

        Overwrites any previous value recorded for the specified input name.

        Examples
            .. code-block:: python

                # log input dataset s3 location
                my_tracker.log_input(name='input', value='s3://inputs/path')

        Args:
            name (str): The name of the input value.
            value (str): The value.
            media_type (str, optional): The MediaType (MIME type) of the value
        """
        if len(self.trial_component.input_artifacts) >= 30:
            raise ValueError("Cannot add more than 30 input_artifacts under tracker trial_component.")
        self.trial_component.input_artifacts[name] = api_types.TrialComponentArtifact(value, media_type=media_type)

    def log_output(self, name, value, media_type=None):
        """Record a single output artifact for this trial component.

        Overwrites any previous value recorded for the specified output name.

        Examples
            .. code-block:: python

                # log output dataset s3 location
                my_tracker.log_output(name='prediction', value='s3://outputs/path')

        Args:
            name (str): The name of the output value.
            value (str): The value.
            media_type (str, optional): The MediaType (MIME type) of the value.
        """
        if len(self.trial_component.output_artifacts) >= 30:
            raise ValueError("Cannot add more than 30 output_artifacts under tracker trial_component")
        self.trial_component.output_artifacts[name] = api_types.TrialComponentArtifact(value, media_type=media_type)

    def log_artifacts(self, directory, media_type=None):
        """Upload all the files under the directory to s3 and store it as artifacts in this trial component. The file
        name is used as the artifact name

        Examples
            .. code-block:: python

                # log local artifact
                my_tracker.log_artifact(directory='/local/path)

        Args:
            directory (str): The directory of the local files to upload.
            media_type (str, optional): The MediaType (MIME type) of the file. If not specified, this library
                will attempt to infer the media type from the file extension of ``file_path``.
        """
        for dir_file in os.listdir(directory):
            file_path = join(directory, dir_file)
            artifact_name = os.path.splitext(dir_file)[0]
            self.log_artifact(file_path=file_path, name=artifact_name, media_type=media_type)

    def log_artifact(self, file_path, name=None, media_type=None):
        """Legacy overload method to prevent breaking existing code.

        Examples
            .. code-block:: python

                # log a local file
                my_tracker.log_artifact('output/artifact_data.csv', name='prediction')

        Args:
            file_path (str): Path to the file to log.
            name (str, optional): Name of the artifact. Defaults to None.
            media_type (str, optional): Media type of the artifact. Defaults to None.
        """
        self.log_output_artifact(file_path, name, media_type)

    def log_output_artifact(self, file_path, name=None, media_type=None):
        """Upload a local file to s3 and store it as an output artifact in this trial component.

        Examples
            .. code-block:: python

                # log local artifact
                my_tracker.log_output_artifact(file_path='/local/path/artifact.tar.gz')

        Args:
            file_path (str): The path of the local file to upload.
            name (str, optional): The name of the artifact.
            media_type (str, optional): The MediaType (MIME type) of the file. If not specified, this library
                will attempt to infer the media type from the file extension of ``file_path``.
        """
        if len(self.trial_component.output_artifacts) >= 30:
            raise ValueError("Cannot add more than 30 output_artifacts under tracker trial_component")
        media_type = media_type or _guess_media_type(file_path)
        name = name or _resolve_artifact_name(file_path)
        s3_uri, etag = self._artifact_uploader.upload_artifact(file_path)
        self.trial_component.output_artifacts[name] = api_types.TrialComponentArtifact(
            value=s3_uri, media_type=media_type
        )
        self._lineage_artifact_tracker.add_output_artifact(name, s3_uri, etag, media_type)

    def log_input_artifact(self, file_path, name=None, media_type=None):
        """Upload a local file to s3 and store it as an input artifact in this trial component.

        Examples
            .. code-block:: python

                # log local artifact
                my_tracker.log_input_artifact(file_path='/local/path/artifact.tar.gz')

        Args:
            file_path (str): The path of the local file to upload.
            name (str, optional): The name of the artifact.
            media_type (str, optional): The MediaType (MIME type) of the file. If not specified, this library
                will attempt to infer the media type from the file extension of ``file_path``.
        """
        if len(self.trial_component.input_artifacts) >= 30:
            raise ValueError("Cannot add more than 30 input_artifacts under tracker trial_component.")
        media_type = media_type or _guess_media_type(file_path)
        name = name or _resolve_artifact_name(file_path)
        s3_uri, etag = self._artifact_uploader.upload_artifact(file_path)
        self.trial_component.input_artifacts[name] = api_types.TrialComponentArtifact(
            value=s3_uri, media_type=media_type
        )
        self._lineage_artifact_tracker.add_input_artifact(name, s3_uri, etag, media_type)

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        """Record a scalar metric value for this TrialComponent to file, not SageMaker.

        Examples
            .. code-block:: python

                for epoch in range(epochs):
                    # your training logic and calculate accuracy and loss
                    my_tracker.log_metric(metric_name='accuracy', value=0.9, iteration_number=epoch)
                    my_tracker.log_metric(metric_name='loss', value=0.03, iteration_number=epoch)

        Args:
            metric_name (str): The name of the metric.
            value (number): The value of the metric.
            timestamp (datetime.datetime|number, optional): The timestamp of the metric. If specified, should
                either be a datetime.datetime object or a number representing the seconds since
                the epoch. If not specified, the current local time will be used.
            iteration_number (number, optional): The integer iteration number of the metric value.

        Raises:
            AttributeError: If the metrics writer is not initialized.
        """
        try:
            self._metrics_writer.log_metric(metric_name, value, timestamp, iteration_number)
        except AttributeError:
            if not self._metrics_writer:
                if not self._warned_on_metrics:
                    logging.warning("Cannot write metrics in this environment.")
                    self._warned_on_metrics = True
            else:
                raise

    def log_table(self, title=None, values=None, data_frame=None, output_artifact=True):
        """Record a table of values that will be rendered in Studio.

        Note that this method must be run from a SageMaker context such as studio or training job
        due to restrictions on the CreateArtifact API.


        Examples
            .. code-block:: python

                table_data = {
                    "x": [1,2,3],
                    "y": [4,5,6]
                }
                my_tracker.log_table('SampleData',table_data)

                # or log a data frame
                df = pd.DataFrame(data=table_data)
                my_tracker.log_table('SampleData',df)

        Args:
            title (str, optional): Title of the table. Defaults to None.
            values ([type], optional): A dictionary of values. i.e. {"x": [1,2,3], "y": [1,2,3]}.
                Defaults to None.
            data_frame (DataFrame, optional): Pandas dataframe alternative to values.
                Defaults to None.
            output_artifact (bool): Determines direction of association to the trial component.
                Defaults to output artifact. If False will be an input artifact.

        Raises:
            ValueError: If values or data_frame are invalid.
        """
        if values is None and data_frame is None:
            raise ValueError("Either values or data_frame must be supplied.")

        if values is not None and data_frame is not None:
            raise ValueError("Only one of values or data_frame may be supplied.")

        if values is not None:
            for key in values:
                if "list" not in str(type(values[key])):
                    raise ValueError(
                        'Table values should be list. i.e. {"x": [1,2,3]}, instead was ' + str(type(values[key]))
                    )

        if data_frame:
            values = _ArtifactConverter.convert_data_frame_to_values(data_frame)
            fields = _ArtifactConverter.convert_data_frame_to_fields(data_frame)
        else:
            fields = _ArtifactConverter.convert_dict_to_fields(values)

        data = {"type": "Table", "version": 0, "title": title, "fields": fields, "data": values}

        self._log_graph_artifact(title, data, "Table", output_artifact)

    def _log_precision_recall(
        self,
        y_true,
        predicted_probabilities,
        positive_label=None,
        title=None,
        output_artifact=True,
    ):
        """Log a precision recall graph artifact which will be displayed in studio.
            Requires sklearn.  Not yet supported by studio.

        Note that this method must be run from a SageMaker context such as studio or training job
        due to restrictions on the CreateArtifact API.

        Examples
            .. code-block:: python

                y_true = [0, 0, 1, 1]
                y_scores = [0.1, 0.4, 0.35, 0.8]

                my_tracker._log_precision_recall(y_true, y_scores)

        Args:
            y_true (array): True labels. If labels are not binary then positive_label should be given.
            predicted_probabilities (array): Estimated/predicted probabilities.
            positive_label (str or int, optional): Label of the positive class. Defaults to None.
            title (str, optional): Title of the graph, Defaults to none.
            output_artifact (boolean, optional): Determines if the artifact is associated with the
                Trial Component as an output artifact. If False will be an input artifact.

        Raises:
            ValueError: If mismatch between y_true and predicted_probabilities.
        """

        if len(y_true) != len(predicted_probabilities):
            raise ValueError("Mismatch between actual values and predicted probabilities.")

        get_module("sklearn")
        from sklearn.metrics import precision_recall_curve, average_precision_score

        kwargs = {}
        if positive_label:
            kwargs["positive_label"] = positive_label

        precision, recall, thresholds = precision_recall_curve(y_true, predicted_probabilities, **kwargs)

        kwargs["average"] = "micro"
        ap = average_precision_score(y_true, predicted_probabilities, **kwargs)

        data = {
            "type": "PrecisionRecallCurve",
            "version": 0,
            "title": title,
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "averagePrecisionScore": ap,
        }
        self._log_graph_artifact(title, data, "PrecisionRecallCurve", output_artifact)

    def log_roc_curve(
        self,
        y_true,
        y_score,
        title=None,
        output_artifact=True,
    ):
        """Log a receiver operating characteristic (ROC) artifact which will be displayed in
        studio.  Requires sklearn.

        Note that this method must be run from a SageMaker context such as studio or training job
        due to restrictions on the CreateArtifact API.

        Examples
            .. code-block:: python

                y_true = [0, 0, 1, 1]
                y_scores = [0.1, 0.4, 0.35, 0.8]

                my_tracker.log_roc_curve(y_true, y_scores)

        Args:
            y_true (array): True labels. If labels are not binary then positive_label should be given.
            y_score (array): Estimated/predicted probabilities.
            title (str, optional): Title of the graph, Defaults to none.
            output_artifact (boolean, optional): Determines if the artifact is associated with the
                Trial Component as an output artifact. If False will be an input artifact.

        Raises:
            ValueError: If mismatch between y_true and predicted_probabilities.
        """

        if len(y_true) != len(y_score):
            raise ValueError("Mismatch between actual labels and predicted scores.")

        get_module("sklearn")
        from sklearn.metrics import roc_curve, auc

        fpr, tpr, thresholds = roc_curve(y_true, y_score)

        auc = auc(fpr, tpr)

        data = {
            "type": "ROCCurve",
            "version": 0,
            "title": title,
            "falsePositiveRate": fpr.tolist(),
            "truePositiveRate": tpr.tolist(),
            "areaUnderCurve": auc,
        }
        self._log_graph_artifact(title, data, "ROCCurve", output_artifact)

    def _log_graph_artifact(self, name, data, graph_type, output_artifact):
        """Logs an artifact by uploading data to S3, creating an artifact, and associating that
        artifact with the tracker's Trial Component.

        Args:
            name (str): Name of the artifact.
            data (dict): Artifacts data that will be saved to S3.
            graph_type (str):  The type of the artifact.
            output_artifact (bool): Determines the direction of association with the
                trial component. Defaults to True (output association). If False will be input
                association.
        """
        # generate an artifact name
        artifact_name = name
        if not artifact_name:
            artifact_name = (
                graph_type + "-" + str(datetime.datetime.now(dateutil.tz.tzlocal()).timestamp()).split(".")[0]
            )

        # create a json file in S3
        s3_uri, etag = self._artifact_uploader.upload_object_artifact(artifact_name, data, file_extension="json")

        # create an artifact and association for the table
        if output_artifact:
            self._lineage_artifact_tracker.add_output_artifact(artifact_name, s3_uri, etag, graph_type)
        else:
            self._lineage_artifact_tracker.add_input_artifact(artifact_name, s3_uri, etag, graph_type)

    def __enter__(self):
        """Updates the start time of the tracked trial component.

        Returns:
            obj: self.
        """
        self._start_time = datetime.datetime.now(dateutil.tz.tzlocal())
        if not self._in_sagemaker_job:
            self.trial_component.start_time = self._start_time
            self.trial_component.status = api_types.TrialComponentStatus(primary_status="InProgress")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Updates the end time of the tracked trial component.
        exc_value (str): The exception value.
        exc_traceback (str): The stack trace of the exception.
        """
        self._end_time = datetime.datetime.now(dateutil.tz.tzlocal())
        if not self._in_sagemaker_job:
            self.trial_component.end_time = self._end_time
            if exc_value:
                self.trial_component.status = api_types.TrialComponentStatus(
                    primary_status="Failed", message=str(exc_value)
                )
            else:
                self.trial_component.status = api_types.TrialComponentStatus(primary_status="Completed")
        self.close()

    def close(self):
        """Close this tracker and save state to SageMaker."""
        try:
            # update the trial component with additions from tracker
            self.trial_component.save()
            # create lineage entities for the artifacts
            self._lineage_artifact_tracker.save()
        finally:
            if self._metrics_writer:
                self._metrics_writer.close()


def _resolve_artifact_name(file_path):
    _, filename = os.path.split(file_path)
    if filename:
        return filename
    else:
        return _utils.name("artifact")


class _ArtifactUploader(object):
    def __init__(self, trial_component_name, artifact_bucket, artifact_prefix, boto_session):
        self.s3_client = boto_session.client("s3")
        self.boto_session = boto_session
        self.trial_component_name = trial_component_name
        self.artifact_bucket = artifact_bucket
        self.artifact_prefix = artifact_prefix or "trial-component-artifacts"

    def upload_artifact(self, file_path):
        """Upload an artifact file to S3 and record the artifact S3 key with this trial run.

        Args:
            file_path (str): the file path of the artifact

        Returns:
            (str, str): The s3 URI of the uploaded file and the etag of the file.

        Raises:
            ValueError: If file does not exist.
        """
        file_path = os.path.expanduser(file_path)
        if not os.path.isfile(file_path):
            raise ValueError("{} does not exist or is not a file. Please supply a file path.".format(file_path))
        if not self.artifact_bucket:
            self.artifact_bucket = _utils.get_or_create_default_bucket(self.boto_session)
        artifact_name = os.path.basename(file_path)
        artifact_s3_key = "{}/{}/{}".format(self.artifact_prefix, self.trial_component_name, artifact_name)
        self.s3_client.upload_file(file_path, self.artifact_bucket, artifact_s3_key)
        etag = self._try_get_etag(artifact_s3_key)
        return "s3://{}/{}".format(self.artifact_bucket, artifact_s3_key), etag

    def upload_object_artifact(self, artifact_name, obj, file_extension=None):
        """Upload an artifact object to S3 and record the artifact S3 key with this trial component.

        Args:
            artifact_name (str): the name of the artifact.
            obj (obj): the object of the artifact
            file_extension (str): Optional file extension.

        Returns:
            str: The s3 URI of the uploaded file and the version of the file
        """
        if not self.artifact_bucket:
            self.artifact_bucket = _utils.get_or_create_default_bucket(self.boto_session)
        if file_extension:
            artifact_name = artifact_name + ("" if file_extension.startswith(".") else ".") + file_extension
        artifact_s3_key = "{}/{}/{}".format(self.artifact_prefix, self.trial_component_name, artifact_name)
        self.s3_client.put_object(Body=json.dumps(obj), Bucket=self.artifact_bucket, Key=artifact_s3_key)
        etag = self._try_get_etag(artifact_s3_key)

        return "s3://{}/{}".format(self.artifact_bucket, artifact_s3_key), etag

    def _try_get_etag(self, key):
        try:
            response = self.s3_client.head_object(Bucket=self.artifact_bucket, Key=key)
            return response["ETag"]
        except botocore.exceptions.ClientError:
            # requires read permissions
            pass
        return None


def _guess_media_type(file_path):
    """Guesses the media type of a file based on its file name.

    Args:
        file_path (str): Path to file.

    Returns:
        str: The guessed media type.
    """
    file_url = urllib.parse.urljoin("file:", urllib.request.pathname2url(file_path))
    guessed_media_type, _ = mimetypes.guess_type(file_url, strict=False)
    return guessed_media_type


class _LineageArtifactTracker(object):
    def __init__(self, trial_component_arn, sagemaker_client):
        self.trial_component_arn = trial_component_arn
        self.sagemaker_client = sagemaker_client
        self.artifacts = []

    def add_input_artifact(self, name, source_uri, etag, artifact_type):
        artifact = _LineageArtifact(
            name, source_uri, etag, dest_arn=self.trial_component_arn, artifact_type=artifact_type
        )
        self.artifacts.append(artifact)

    def add_output_artifact(self, name, source_uri, etag, artifact_type):
        artifact = _LineageArtifact(
            name, source_uri, etag, source_arn=self.trial_component_arn, artifact_type=artifact_type
        )
        self.artifacts.append(artifact)

    def save(self):
        for artifact in self.artifacts:
            artifact.create_artifact(self.sagemaker_client)
            artifact.add_association(self.sagemaker_client)


class _LineageArtifact(object):
    def __init__(self, name, source_uri, etag, source_arn=None, dest_arn=None, artifact_type=None):
        self.name = name
        self.source_uri = source_uri
        self.etag = etag
        self.source_arn = source_arn
        self.dest_arn = dest_arn
        self.artifact_arn = None
        self.artifact_type = artifact_type if artifact_type else "Tracker"

    def create_artifact(self, sagemaker_client):
        source_ids = []
        if self.etag:
            source_ids.append({"SourceIdType": "S3ETag", "Value": self.etag})

        response = sagemaker_client.create_artifact(
            ArtifactName=self.name,
            ArtifactType=self.artifact_type,
            Source={"SourceUri": self.source_uri, "SourceTypes": source_ids},
        )
        self.artifact_arn = response["ArtifactArn"]

    def add_association(self, sagemaker_client):
        source_arn = self.source_arn if self.source_arn else self.artifact_arn
        dest_arn = self.dest_arn if self.dest_arn else self.artifact_arn
        # if the trial component (job) is the source then it produced the artifact, otherwise the
        # artifact contributed to the trial component (job)
        association_edge_type = "Produced" if self.source_arn else "ContributedTo"
        sagemaker_client.add_association(
            SourceArn=source_arn, DestinationArn=dest_arn, AssociationType=association_edge_type
        )


class _ArtifactConverter(object):
    """Converts data to easily consumed by studio."""

    @classmethod
    def convert_dict_to_fields(cls, values):
        """Converts a dictionary to list of field types.

        Args:
            values (dict): The values of the dictionary.

        Returns:
            dict: Dictionary of fields.
        """
        fields = []
        for key in values:
            fields.append({"name": key, "type": "string"})
        return fields

    @classmethod
    def convert_data_frame_to_values(cls, data_frame):
        """Converts a pandas data frame to a dictionary in the table artifact format.

        Args:
            data_frame (DataFrame): The pandas data frame to convert.

        Returns:
            [type]: dictionary of values in the format needed to log the artifact.
        """
        df_dict = data_frame.to_dict()
        new_df = {}
        for key in df_dict:
            col_value = df_dict[key]
            values = []

            for row_key in col_value:
                values.append(col_value[row_key])

            new_df[key] = values

        return new_df

    @classmethod
    def convert_data_frame_to_fields(cls, data_frame):
        """Converts a dataframe to a dictionary describing the type of fields.

        Args:
            data_frame(str): The data frame to convert.

        Returns:
            dict: Dictionary of fields.
        """
        fields = []

        for key in data_frame:
            col_type = data_frame.dtypes[key]
            fields.append({"name": key, "type": _ArtifactConverter.convert_df_type_to_simple_type(col_type)})
        return fields

    @classmethod
    def convert_df_type_to_simple_type(cls, data_frame_type):
        """Converts a dataframe type to a type for rendering a table in Studio.

        Args:
            data_frame_type (str): The pandas type.

        Returns:
            str: The type of the table field.
        """

        type_pairs = [
            ("datetime", "datetime"),
            ("float", "number"),
            ("int", "number"),
            ("uint", "number"),
            ("boolean", "boolean"),
        ]
        for pair in type_pairs:
            if str(data_frame_type).lower().startswith(pair[0]):
                return pair[1]
        return "string"
