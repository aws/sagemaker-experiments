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
import datetime
import os
import mimetypes
import time
import urllib.parse
import urllib.request


import dateutil

from smexperiments import api_types, metrics, trial_component, _utils


RESOLVE_JOB_INTERVAL_SECONDS = 2
RESOLVE_JOB_TIMEOUT_SECONDS = 30


class Tracker(object):

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

    @classmethod
    def load(cls, trial_component_name=None, artifact_bucket=None, artifact_prefix=None,
             boto3_session=None, sagemaker_boto_client=None):
        boto3_session = boto3_session or _utils.boto_session()
        sagemaker_boto_client = sagemaker_boto_client or _utils.sagemaker_client()

        # Resolve the trial component for this tracker to track: If a trial component name was passed in, then load
        # and track that trial component. Otherwise, try to find a trial component given the current environment,
        # failing if we're unable to load one.
        if trial_component_name:
            tc = trial_component.TrialComponent.load(trial_component_name=trial_component_name,
                                                     sagemaker_boto_client=sagemaker_boto_client)
        else:
            tc = _resolve_trial_component_for_job(sagemaker_boto_client)
            if not tc:
                raise ValueError('Could not load TrialComponent. Specify a trial_component_name or invoke "create"')

        # Create a metrics writer if we are in a SageMaker Training Job
        if _utils.resolve_environment_type() == _utils.EnvironmentType.SageMakerTrainingJob:
            metrics_writer = metrics.SageMakerFileMetricsWriter()
        else:
            metrics_writer = None

        tracker = cls(tc,
                      metrics_writer,
                      _ArtifactUploader(tc.trial_component_name, artifact_bucket, artifact_prefix, boto3_session))
        tracker._in_sagemaker_job = False if trial_component_name else True
        return tracker

    @classmethod
    def create(cls, display_name=None, artifact_bucket=None, artifact_prefix=None, boto3_session=None,
               sagemaker_boto_client=None):
        boto3_session = boto3_session or _utils.boto_session()
        sagemaker_boto_client = sagemaker_boto_client or _utils.sagemaker_client()

        tc = trial_component.TrialComponent.create(
            trial_component_name=_utils.name('TrialComponent'),
            display_name=display_name,
            sagemaker_boto_client=sagemaker_boto_client)
        return cls(tc,
                   None,
                   _ArtifactUploader(tc.trial_component_name, artifact_bucket, artifact_prefix, boto3_session))

    def log_parameter(self, name, value):
        """Record a single parameter value for this trial component. Overwrites any previous value
        recorded for the specified parameter name.
        Args:
            name (str): The name of the parameter
            value (str or numbers.Number): The value of the parameter
        """
        self.trial_component.parameters[name] = value

    def log_parameters(self, parameters):
        """Record a collection of parameter values for this trial component.
        Args:
            parameters (dict[str, str or numbers.Number]): The parameters to record.
        """
        self.trial_component.parameters.update(parameters)

    def log_input(self, name, value, media_type=None):
        """Record a single input artifact for this trial component. Overwrites any previous value
        recorded for the specified input name.
        Args:
            name (str): The name of the input value.
            value (str): The value.
            media_type (str): The MediaType (MIME type) of the value
        """
        self.trial_component.input_artifacts[name] = api_types.TrialComponentArtifact(value, media_type=media_type)

    def log_output(self, name, value, media_type=None):
        """Record a single output artifact for this trial component. Overwrites any previous value
        recorded for the specified output name.
        Args:
            name (str): The name of the output value.
            value (str): The value.
            media_type (str): The MediaType (MIME type) of the value
        """
        self.trial_component.output_artifacts[name] = api_types.TrialComponentArtifact(value, media_type=media_type)

    def log_artifact(self, file_path, name=None, media_type=None):
        media_type = media_type or _guess_media_type(file_path)
        name = name or _resolve_artifact_name(file_path)
        s3_uri = self._artifact_uploader.upload_artifact(file_path)
        self.trial_component.output_artifacts[name] = api_types.TrialComponentArtifact(
            value=s3_uri, media_type=media_type
        )

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        try:
            self._metrics_writer.log_metric(metric_name, value, timestamp, iteration_number)
        except AttributeError:
            if not self._metrics_writer:
                raise SageMakerTrackerException('Logging metrics is not available in this environment')
            else:
                raise

    def __enter__(self):
        self._start_time = datetime.datetime.now(dateutil.tz.tzlocal())
        if not self._in_sagemaker_job:
            self.trial_component.start_time = self._start_time
            self.trial_component.status = api_types.TrialComponentStatus(primary_status='InProgress')
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._end_time = datetime.datetime.now(dateutil.tz.tzlocal())
        if not self._in_sagemaker_job:
            self.trial_component.end_time = self._end_time
            if exc_value:
                self.trial_component.status = api_types.TrialComponentStatus(primary_status='Failed',
                                                                             message=str(exc_value))
            else:
                self.trial_component.status = api_types.TrialComponentStatus(primary_status='Completed')
        self.close()

    def close(self):
        try:
            self.trial_component.save()
        finally:
            if self._metrics_writer:
                self._metrics_writer.close()


class SageMakerTrackerException(Exception):

    def __init__(self, message):
        super().__init__(message)


def _resolve_artifact_name(file_path):
    _, filename = os.path.split(file_path)
    if filename:
        return filename
    else:
        return _utils.name('artifact')


class _ArtifactUploader(object):

    def __init__(self, trial_component_name, artifact_bucket, artifact_prefix, boto_session):
        self.s3_client = boto_session.client('s3')
        self.boto_session = boto_session
        self.trial_component_name = trial_component_name
        self.artifact_bucket = artifact_bucket
        self.artifact_prefix = artifact_prefix or 'trial-component-artifacts'

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


def _resolve_trial_component_for_job(sagemaker_boto_client):
    start = time.time()
    source_arn = _utils.resolve_source_arn_from_environment()
    while source_arn and time.time() - start < RESOLVE_JOB_TIMEOUT_SECONDS:
        summaries = list(trial_component.TrialComponent.list(
            source_arn=source_arn, sagemaker_boto_client=sagemaker_boto_client))
        if summaries:
            summary = summaries[0]
            return trial_component.TrialComponent.load(
                trial_component_name=summary.trial_component_name,
                sagemaker_boto_client=sagemaker_boto_client
            )
        else:
            time.sleep(RESOLVE_JOB_INTERVAL_SECONDS)
    return None


def _guess_media_type(file_path):
    file_url = urllib.parse.urljoin('file:', urllib.request.pathname2url(file_path))
    guessed_media_type, _ = mimetypes.guess_type(file_url, strict=False)
    return guessed_media_type
