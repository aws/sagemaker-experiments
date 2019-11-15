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
"""Placeholder docstring"""
from smexperiments import _base_types, api_types


class TrialComponent(_base_types.Record):
    """
    This class represents a SageMaker TrialComponent object. A TrialComponent represents a stage in
    a trial.
    """

    trial_component_name = None
    trial_component_arn = None
    display_name = None
    source = None
    status = None
    start_time = None
    end_time = None
    creation_time = None
    created_by = None
    last_modified_time = None
    last_modified_by = None
    parameters = None
    input_artifacts = None
    output_artifacts = None
    metrics = None

    _boto_load_method = "describe_trial_component"
    _boto_create_method = "create_trial_component"
    _boto_update_method = "update_trial_component"
    _boto_delete_method = "delete_trial_component"

    _custom_boto_types = {
        "source": (api_types.TrialComponentSource, False),
        "status": (api_types.TrialComponentStatus, False),
        "parameters": (api_types.TrialComponentParameters, False),
        "input_artifacts": (api_types.TrialComponentArtifact, True),
        "output_artifacts": (api_types.TrialComponentArtifact, True),
        "metrics": (api_types.TrialComponentMetricSummary, True)
    }

    _boto_update_members = [
        "trial_component_name",
        "display_name",
        "status",
        "start_time",
        "end_time",
        "parameters",
        "input_artifacts",
        "output_artifacts",
    ]
    _boto_delete_members = ["trial_component_name"]

    def save(self):
        """Placeholder docstring"""
        return self._invoke_api(self._boto_update_method, self._boto_update_members)

    def delete(self):
        """Placeholder docstring"""
        self._invoke_api(self._boto_delete_method, self._boto_delete_members)

    @classmethod
    def load(cls, trial_component_name, sagemaker_boto_client=None):
        """
        Load an existing trial component and return an ``TrialComponent`` object representing it.
        Args:
            trial_component_name: (str): Name of the experiment
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.
        Returns:
            sagemaker.experiments.experiment.Experiment: A SageMaker ``Experiment`` object
        """
        trial_component = cls._construct(
            cls._boto_load_method,
            trial_component_name=trial_component_name,
            sagemaker_boto_client=sagemaker_boto_client,
        )
        return trial_component

    @classmethod
    def create(cls, trial_component_name, display_name=None, sagemaker_boto_client=None):
        """
        Create a trial component and return a ``TrialComponent`` object representing it.

        Returns:
            sagemaker.experiments.trial_component.TrialComponent: A SageMaker ``TrialComponent``
                object.
        """
        return super(TrialComponent, cls)._construct(
            cls._boto_create_method,
            trial_component_name=trial_component_name,
            display_name=display_name,
            sagemaker_boto_client=sagemaker_boto_client)

    @classmethod
    def list(cls, trial_name=None, experiment_name=None, source_arn=None, created_before=None, created_after=None,
             sort_by=None, sort_order=None, sagemaker_boto_client=None):
        """
        Returns the list of trial components in a given trial.
        Args:
            trial_name (str) : Name of the trial.
            sagemaker_boto_client (SageMaker.Client, optional) : Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.
        Returns:
            collections.Iterator[sagemaker.experiments.trial_component.TrialComponent]: An iterator
                over ``TrialComponent`` objects in the trial.
        """
        return super(TrialComponent, cls)._list(
            "list_trial_components",
            api_types.TrialComponentSummary.from_boto,
            "TrialComponentSummaries",
            trial_name=trial_name,
            experiment_name=experiment_name,
            source_arn=source_arn,
            created_before=created_before,
            created_after=created_after,
            sort_by=sort_by,
            sort_order=sort_order,
            sagemaker_boto_client=sagemaker_boto_client)