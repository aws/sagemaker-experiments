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
"""Contains API objects for SageMaker experiments."""
import numbers

from smexperiments import _base_types


class ExperimentSummary(_base_types.ApiObject):
    """Summary model of an experiment.

    Attributes:
        experiment_arn (str): ARN of the experiment.
        experiment_name (str): Name of the experiment.
        creation_time (datetime): Date experiment was created.
        last_modified_time (datetime): Date experiment was last modified.
    """

    experiment_arn = None
    experiment_name = None
    creation_time = None
    last_modified_time = None

    def __init__(self, experiment_name=None, experiment_arn=None, **kwargs):
        super(ExperimentSummary, self).__init__(
            experiment_name=experiment_name, experiment_arn=experiment_arn, **kwargs
        )


class TrialComponentMetricSummary(_base_types.ApiObject):
    """Summary model of a trial component.

    Attributes:
        metric_name (str): The name of the metric.
        source_arn (str):  The ARN of the source.
        time_stamp (datetime): Metric last updated value.
        logical_time (datetime):
        max (float): The max value of the metric.
        min (float):  The min value of the metric.
        last (float):  The last value of the metric.
        count (float):  The number of samples used to generate the metric.
        avg (float):  The average value of the metric.
        std_dev (float):  The standard deviation of the metric.
    """

    metric_name = None
    source_arn = None
    time_stamp = None
    logical_time = None
    max = None
    min = None
    last = None
    count = None
    avg = None
    std_dev = None

    def __init__(self, metric_name=None, source_arn=None, **kwargs):
        super(TrialComponentMetricSummary, self).__init__(metric_name=metric_name, source_arn=source_arn, **kwargs)


class TrialSummary(_base_types.ApiObject):
    """Summary model of a trial.

    Attributes:
        trial_arn (str): The ARN of the trial.
        trial_name (str): The name of the trial.
        creation_time (datetime):  When the trial was created.
        last_modified_time (datetime): When the trial was last modified.
    """

    trial_arn = None
    trial_name = None
    creation_time = None
    last_modified_time = None

    def __init__(self, trial_name=None, trial_arn=None, **kwargs):
        super(TrialSummary, self).__init__(trial_name=trial_name, trial_arn=trial_arn, **kwargs)


class TrialComponentParameterValue(_base_types.ApiObject):
    """Value of a trial component parameter.

    Attributes:
        string_value (str):  The string value of the parameter value.
        number_value (float):  The number value of the parameter value if applicable.
    """

    string_value = None
    number_value = None

    def __init__(self, string_value=None, number_value=None, **kwargs):
        super(TrialComponentParameterValue, self).__init__(
            string_value=string_value, number_value=number_value, **kwargs
        )

    def __str__(self):
        """String representation of TrialComponentParameterValue"""
        if self.string_value is not None:
            return self.string_value
        if self.number_value is not None:
            return str(self.number_value)
        return ""


class TrialComponentParameters(_base_types.ApiObject):
    """A dictionary of TrialComponentParameterValues"""

    @classmethod
    def from_boto(cls, boto_dict, **kwargs):
        """Converts a boto dict to a dictionary of TrialComponentParameterValues

        Args:
            boto_dict (dict): boto response dictionary.
            **kwargs:  Arbitrary keyword arguments.

        Returns:
            dict: Dictionary of parameter values.
        """
        return_map = {}
        for key, value in boto_dict.items():
            return_map[key] = value.get("NumberValue", value.get("StringValue", None))
        return return_map

    @classmethod
    def to_boto(self, parameters):
        """Converts TrialComponentParameters to dict.

        Args:
            parameters (TrialComponentParameters): Dictionary to convert.

        Returns:
            dict: Dictionary of trial component parameters in boto format.
        """
        boto_map = {}
        for key, value in parameters.items():
            if isinstance(value, numbers.Number):
                boto_map[key] = {"NumberValue": value}
            else:
                boto_map[key] = {"StringValue": str(value)}
        return boto_map


class TrialComponentArtifact(_base_types.ApiObject):
    """Trial component artifact.

    Attributes:
        media_type (str): The media type.
        value (str): The artifact value.
    """

    media_type = None
    value = None

    def __init__(self, value=None, media_type=None, **kwargs):
        super(TrialComponentArtifact, self).__init__(value=value, media_type=media_type, **kwargs)


class TrialComponentStatus(_base_types.ApiObject):
    """Status of the trial component.

    Attributes:
        primary_status (str): The status of a trial component.
        message (str): Status message.
    """

    primary_status = None
    message = None

    def __init__(self, primary_status=None, message=None, **kwargs):
        super(TrialComponentStatus, self).__init__(primary_status=primary_status, message=message, **kwargs)


class TrialComponentSummary(_base_types.ApiObject):
    """Summary model of a trial component.

    Attributes:
        trial_component_name (str): Name of trial component.
        trial_component_arn (str): ARN of the trial component.
        display_name (str): Friendly display name.
        source_arn (str): ARN of the trial component source.
        status (str): Status.
        start_time (datetime): Start time.
        end_time (datetime): End time.
        creation_time (datetime): Creation time.
        created_by (str): Created by.
        last_modified_time (datetime): Date last modified.
        last_modified_by (datetime): User last modified.
    """

    _custom_boto_types = {
        "status": (TrialComponentStatus, False),
    }
    trial_component_name = None
    trial_component_arn = None
    display_name = None
    source_arn = None
    status = None
    start_time = None
    end_time = None
    creation_time = None
    created_by = None
    last_modified_time = None
    last_modified_by = None

    def __init__(self, **kwargs):
        super(TrialComponentSummary, self).__init__(**kwargs)


class ExperimentSource(_base_types.ApiObject):
    """ExperimentSource

    Attributes:
        source_arn (str): The ARN of the source.
    """

    source_arn = None

    def __init__(self, source_arn=None, **kwargs):
        super(ExperimentSource, self).__init__(source_arn=source_arn, **kwargs)


class TrialSource(_base_types.ApiObject):
    """TrialSource

    Attributes:
        source_arn (str): The ARN of the source.
    """

    source_arn = None

    def __init__(self, source_arn=None, **kwargs):
        super(TrialSource, self).__init__(source_arn=source_arn, **kwargs)


class TrialComponentSource(_base_types.ApiObject):
    """TrialComponentsource

    Attributes:
        source_arn (str): The ARN of the source.
    """

    source_arn = None

    def __init__(self, source_arn=None, **kwargs):
        super(TrialComponentSource, self).__init__(source_arn=source_arn, **kwargs)


class BatchPutMetricsError(_base_types.ApiObject):
    """BatchPutMetricsError

    Attributes:
        code (str): The error code.
        message (str): The error message.
        metric_index (int): The index of the metric.

    """

    code = None
    message = None
    metric_index = None

    def __init__(self, code=None, message=None, metric_index=None, **kwargs):
        super(BatchPutMetricsError, self).__init__(code=code, message=message, metric_index=metric_index, **kwargs)


class TrainingJobSearchResult(_base_types.ApiObject):
    """Summary model of an Training Job search result.

    Attributes:
        training_job_name (str): The name of the training job.
        training_job_arn (str): The Amazon Resource Name (ARN) of the training job.
        tuning_job_arn (str): The Amazon Resource Name (ARN) of the associated.
        hyperparameter tuning job if the training job was launched by a hyperparameter tuning job.
        labeling_job_arn (str): The Amazon Resource Name (ARN) of the labeling job.
        autoML_job_arn (str): The Amazon Resource Name (ARN) of the job.
        model_artifacts (dict): Information about the Amazon S3 location that is configured for storing model artifacts.
        training_job_status (str): The status of the training job
        hyper_parameters (dict): Algorithm-specific parameters.
        algorithm_specification (dict): Information about the algorithm used for training, and algorithm metadata.
        input_data_config (dict): An array of Channel objects that describes each data input channel.
        output_data_config (dict): The S3 path where model artifacts that you configured when creating the job are
        stored. Amazon SageMaker creates subfolders for model artifacts.
        resource_config (dict): Resources, including ML compute instances and ML storage volumes, that are configured
        for model training.
        debug_hook_config (dict): Configuration information for the debug hook parameters, collection configuration,
        and storage paths.
        debug_rule_config (dict): Information about the debug rule configuration.
    """

    training_job_name = None
    training_job_arn = None
    tuning_job_arn = None
    labeling_job_arn = None
    autoML_job_arn = None
    model_artifacts = None
    training_job_status = None
    hyper_parameters = None
    algorithm_specification = None
    input_data_config = None
    output_data_config = None
    resource_config = None
    debug_hook_config = None
    experiment_config = None
    debug_rule_config = None

    def __init__(
        self,
        training_job_arn=None,
        training_job_name=None,
        tuning_job_arn=None,
        labeling_job_arn=None,
        autoML_job_arn=None,
        model_artifacts=None,
        training_job_status=None,
        hyper_parameters=None,
        algorithm_specification=None,
        input_data_config=None,
        output_data_config=None,
        resource_config=None,
        debug_hook_config=None,
        experiment_config=None,
        debug_rule_config=None,
        **kwargs
    ):
        super(TrainingJobSearchResult, self).__init__(
            training_job_arn=training_job_arn,
            training_job_name=training_job_name,
            tuning_job_arn=tuning_job_arn,
            labeling_job_arn=labeling_job_arn,
            autoML_job_arn=autoML_job_arn,
            model_artifacts=model_artifacts,
            training_job_status=training_job_status,
            hyper_parameters=hyper_parameters,
            algorithm_specification=algorithm_specification,
            input_data_config=input_data_config,
            output_data_config=output_data_config,
            resource_config=resource_config,
            debug_hook_config=debug_hook_config,
            experiment_config=experiment_config,
            debug_rule_config=debug_rule_config,
            **kwargs
        )


class ExperimentSearchResult(_base_types.ApiObject):
    """Summary model of an Experiment search result.

    Attributes:
        experiment_arn (str): ARN of the experiment.
        experiment_name (str): Name of the experiment.
        display_name (str): Display name of the experiment.
        source (dict): The source of the experiment
        tags (list): The list of tags that are associated with the experiment.
    """

    experiment_arn = None
    experiment_name = None
    display_name = None
    source = None
    tags = None

    def __init__(self, experiment_arn=None, experiment_name=None, display_name=None, source=None, tags=None, **kwargs):
        super(ExperimentSearchResult, self).__init__(
            experiment_arn=experiment_arn,
            experiment_name=experiment_name,
            display_name=display_name,
            source=source,
            tags=tags,
            **kwargs
        )


class TrialSearchResult(_base_types.ApiObject):
    """Summary model of an Trial search result.

    Attributes:
        trial_arn (str): ARN of the trial.
        trial_name (str): Name of the trial.
        display_name (str): Display name of the trial.
        source (dict): The source of the trial.
        tags (list): The list of tags that are associated with the trial.
        trial_component_summaries (dict):
    """

    trial_arn = None
    trial_name = None
    display_name = None
    source = None
    tags = None
    trial_component_summaries = None

    def __init__(
        self,
        trial_arn=None,
        trial_name=None,
        display_name=None,
        source=None,
        tags=None,
        trial_component_summaries=None,
        **kwargs
    ):
        super(TrialSearchResult, self).__init__(
            trial_arn=trial_arn,
            trial_name=trial_name,
            display_name=display_name,
            source=source,
            tags=tags,
            trial_component_summaries=trial_component_summaries,
            **kwargs
        )


class TrialComponentSearchResult(_base_types.ApiObject):
    """Summary model of an Trial Component search result.

    Attributes:
        trial_component_arn (str): ARN of the trial component.
        trial_component_name (str): Name of the trial component.
        display_name (str): Display name of the trial component.
        source (dict): The source of the trial component.
        status (dict): The status of the trial component.
        start_time (datetime): Start time.
        end_time (datetime): End time.
        creation_time (datetime): Creation time.
        created_by (str): Created by.
        last_modified_time (datetime): Date last modified.
        last_modified_by (datetime): User last modified.
        parameters (dict): The hyperparameters of the component.
        input_artifacts (dict): The input artifacts of the component.
        output_artifacts (dict): The output artifacts of the component.
        metrics (list): The metrics for the component.
        source_detail (dict): The source of the trial component.
        tags (list): The list of tags that are associated with the trial component.
        parents (dict): The parent of trial component
    """

    trial_component_arn = None
    trial_component_name = None
    display_name = None
    source = None
    status = None
    parameters = None
    input_artifacts = None
    output_artifacts = None
    metrics = None
    source_detail = None
    tags = None
    parents = None

    def __init__(
        self,
        trial_component_arn=None,
        trial_component_name=None,
        start_time=None,
        end_time=None,
        display_name=None,
        source=None,
        status=None,
        parameters=None,
        input_artifacts=None,
        output_artifacts=None,
        metrics=None,
        source_detail=None,
        tags=None,
        parents=None,
        **kwargs
    ):
        super(TrialComponentSearchResult, self).__init__(
            trial_component_arn=trial_component_arn,
            trial_component_name=trial_component_name,
            display_name=display_name,
            source=source,
            status=status,
            parameters=parameters,
            input_artifacts=input_artifacts,
            output_artifacts=output_artifacts,
            metrics=metrics,
            source_detail=source_detail,
            tags=tags,
            parents=parents,
            **kwargs
        )
