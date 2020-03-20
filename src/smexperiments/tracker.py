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
"""Contains the SageMaker Experiments Tracker class."""
import datetime
import os
import mimetypes
import urllib.parse
import urllib.request
import logging

import dateutil

from smexperiments import api_types, metrics, trial_component, _utils, _environment


class Tracker(object):
    """"A SageMaker Experiments Tracker.

    Use a tracker object to record experiment information to a SageMaker trial component.

    A new tracker can be created in two ways:

    - By loading an existing trial component with :meth:`~smexperiments.tracker.Tracker.load`
    - By creating a tracker for a new trial component with :meth:`~smexperiments.tracker.Tracker.create`.

    When creating a tracker within a SageMaker training or processing job, use the ``load`` method with
    no arguments to track artifacts to the trial component automatically created for your job. When tracking
    within a  Jupyternotebook running in SageMaker, use the ``create`` method to automatically create a new
    trial component.

    Trackers are Python context managers and you can use them using the Python ``with`` keyword. Exceptions
    thrown within the with block will cause the tracker's trial component to be marked as failed. Start and
    end times are automatically set when using the with statement and the trial component is saved to
    SageMaker at the end of the block.

    Attributes:
        trial_component (TrialComponent): The trial component tracked.
    """

    trial_component = None
    _metrics_writer = None
    _in_sagemaker_job = False
    _artifact_uploader = None

    def __init__(self, trial_component, metrics_writer, artifact_uploader):
        self.trial_component = trial_component
        self.trial_component.parameters = self.trial_component.parameters or {}
        self.trial_component.input_artifacts = self.trial_component.input_artifacts or {}
        self.trial_component.output_artifacts = self.trial_component.output_artifacts or {}
        self._artifact_uploader = artifact_uploader
        self._metrics_writer = metrics_writer
        self._warned_on_metrics = False

    @classmethod
    def load(
        cls,
        trial_component_name=None,
        artifact_bucket=None,
        artifact_prefix=None,
        boto3_session=None,
        sagemaker_boto_client=None,
    ):
        """Create a new ``Tracker`` by loading an existing trial component.

        Examples:
            .. code-block:: python

                from smexperiments import tracker

                my_tracker = tracker.Tracker.load(trial_component_name='xgboost')

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

        Returns:
            Tracker: The tracker for the given trial component.

        Raises:
            ValueError: If the trial component failed to load.
        """
        boto3_session = boto3_session or _utils.boto_session()
        sagemaker_boto_client = sagemaker_boto_client or _utils.sagemaker_client()

        tce = _environment.TrialComponentEnvironment.load()

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
        self.trial_component.input_artifacts[name] = api_types.TrialComponentArtifact(value, media_type=media_type)

    def log_output(self, name, value, media_type=None):
        """Record a single output artifact for this trial component.

        Overwrites any previous value recorded for the specified output name.

        Examples
            .. code-block:: python

                # log input dataset s3 location
                my_tracker.log_output(name='prediction', value='s3://outputs/path')

        Args:
            name (str): The name of the output value.
            value (str): The value.
            media_type (str, optional): The MediaType (MIME type) of the value.
        """
        self.trial_component.output_artifacts[name] = api_types.TrialComponentArtifact(value, media_type=media_type)

    def log_artifact(self, file_path, name=None, media_type=None):
        """Upload a local file to s3 and store it as an artifact in this trial component.

        Examples
            .. code-block:: python

                # log local artifact
                my_tracker.log_artifact(file_path='/local/path/artifact.tar.gz')

        Args:
            file_path (str): The path of the local file to upload.
            name (str, optional): The name of the artifact.
            media_type (str, optional): The MediaType (MIME type) of the file. If not specified, this library
                will attempt to infer the media type from the file extension of ``file_path``.
        """
        media_type = media_type or _guess_media_type(file_path)
        name = name or _resolve_artifact_name(file_path)
        s3_uri = self._artifact_uploader.upload_artifact(file_path)
        self.trial_component.output_artifacts[name] = api_types.TrialComponentArtifact(
            value=s3_uri, media_type=media_type
        )

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        """Record a scalar metric value for this TrialComponent.

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

    def __enter__(self):
        self._start_time = datetime.datetime.now(dateutil.tz.tzlocal())
        if not self._in_sagemaker_job:
            self.trial_component.start_time = self._start_time
            self.trial_component.status = api_types.TrialComponentStatus(primary_status="InProgress")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
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
            self.trial_component.save()
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
        """Upload an artifact file to S3 and record the artifact S3 key with this trial run."""
        file_path = os.path.expanduser(file_path)
        if not os.path.isfile(file_path):
            raise ValueError("{} does not exist or is not a file. Please supply a file path.".format(file_path))
        if not self.artifact_bucket:
            self.artifact_bucket = _utils.get_or_create_default_bucket(self.boto_session)
        artifact_name = os.path.basename(file_path)
        artifact_s3_key = "{}/{}/{}".format(self.artifact_prefix, self.trial_component_name, artifact_name)
        self.s3_client.upload_file(file_path, self.artifact_bucket, artifact_s3_key)
        return "s3://{}/{}".format(self.artifact_bucket, artifact_s3_key)


def _guess_media_type(file_path):
    file_url = urllib.parse.urljoin("file:", urllib.request.pathname2url(file_path))
    guessed_media_type, _ = mimetypes.guess_type(file_url, strict=False)
    return guessed_media_type
