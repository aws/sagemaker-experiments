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
"""Contains api objects for SageMaker experiments."""
import numbers

from smexperiments import _base_types


class ExperimentSummary(_base_types.ApiObject):
    """
    ExperimentSummary
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
    """
    TrialComponentMetricSummary
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
    """
    TrialSummary
    """

    trial_arn = None
    trial_name = None
    creation_time = None
    last_modified_time = None

    def __init__(self, trial_name=None, trial_arn=None, **kwargs):
        super(TrialSummary, self).__init__(trial_name=trial_name, trial_arn=trial_arn, **kwargs)


class TrialComponentParameterValue(_base_types.ApiObject):
    """
    TrialComponentParameterValue
    """

    string_value = None
    number_value = None

    def __init__(self, string_value=None, number_value=None, **kwargs):
        super(TrialComponentParameterValue, self).__init__(
            string_value=string_value, number_value=number_value, **kwargs
        )

    def __str__(self):
        if self.string_value is not None:
            return self.string_value
        if self.number_value is not None:
            return str(self.number_value)
        return ""


class TrialComponentParameters(_base_types.ApiObject):
    @classmethod
    def from_boto(cls, boto_dict, **kwargs):
        return_map = {}
        for key, value in boto_dict.items():
            return_map[key] = value.get("NumberValue", value.get("StringValue", None))
        return return_map

    @classmethod
    def to_boto(self, parameters):
        boto_map = {}
        for key, value in parameters.items():
            if isinstance(value, numbers.Number):
                boto_map[key] = {"NumberValue": value}
            else:
                boto_map[key] = {"StringValue": str(value)}
        return boto_map


class TrialComponentArtifact(_base_types.ApiObject):
    """
    TrialComponentArtifact
    """

    media_type = None
    value = None

    def __init__(self, value=None, media_type=None, **kwargs):
        super(TrialComponentArtifact, self).__init__(value=value, media_type=media_type, **kwargs)


class TrialComponentStatus(_base_types.ApiObject):
    """TrialComponentStatus"""

    primary_status = None
    message = None

    def __init__(self, primary_status=None, message=None, **kwargs):
        super(TrialComponentStatus, self).__init__(primary_status=primary_status, message=message, **kwargs)


class TrialComponentSummary(_base_types.ApiObject):
    """
    TrialComponentSummary
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
    """ExperimentSource"""

    source_arn = None

    def __init__(self, source_arn=None, **kwargs):
        super(ExperimentSource, self).__init__(source_arn=source_arn, **kwargs)


class TrialSource(_base_types.ApiObject):
    """TrialSource"""

    source_arn = None

    def __init__(self, source_arn=None, **kwargs):
        super(TrialSource, self).__init__(source_arn=source_arn, **kwargs)


class TrialComponentSource(_base_types.ApiObject):
    """TrialComponentsource"""

    source_arn = None

    def __init__(self, source_arn=None, **kwargs):
        super(TrialComponentSource, self).__init__(source_arn=source_arn, **kwargs)


class BatchPutMetricsError(_base_types.ApiObject):
    code = None
    message = None
    metric_index = None

    def __init__(self, code=None, message=None, metric_index=None, **kwargs):
        super(BatchPutMetricsError, self).__init__(code=code, message=message, metric_index=metric_index, **kwargs)
