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
from smexperiments import api_types, _base_types, trial_component, _utils, tracker


class Trial(_base_types.Record):
    """
    An execution of a data-science workflow with an Experiment. Consists of a list of TrialComponent objects, which
    document individual activities within the workflow.
    """

    trial_name = None
    experiment_name = None

    _boto_create_method = "create_trial"
    _boto_load_method = "describe_trial"
    _boto_delete_method = "delete_trial"

    _boto_delete_members = ["trial_name"]

    def update(self):
        """Placeholder docstring"""
        return self._invoke_api(self._boto_update_method, self._boto_update_members)

    def delete(self):
        """Placeholder docstring"""
        self._invoke_api(self._boto_delete_method, self._boto_delete_members)

    @classmethod
    def load(cls, trial_name, sagemaker_boto_client=None):
        """
        Load details about an existing trial and return a ``Trial`` object.
        Args:
            trial_name: (str): Name of the Trial.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.
        Returns:
            sagemaker.experiments.trial.Trial: A SageMaker ``Trial`` object
        """
        return super(Trial, cls)._construct(
            cls._boto_load_method,
            trial_name=trial_name,
            sagemaker_boto_client=sagemaker_boto_client)

    @classmethod
    def create(
        cls,
        experiment_name,
        trial_name=None,
        sagemaker_boto_client=None,
        trial_components=None
    ):
        """
        Create a new trial and return a ``Trial`` object.

        Args:
            experiment_name: (str): Name of the experiment to create this trial in.
            trial_name: (str, optional): Name of the Trial. If not specified, an auto-generated name will be used.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.
            trial_components (list): A list of trial component names, trial components, or trial component trackers
        Returns:
            sagemaker.experiments.trial.Trial: A SageMaker ``Trial`` object
        """
        trial_name = trial_name or _utils.name('Trial')
        trial = super(Trial, cls)._construct(
            cls._boto_create_method,
            trial_name=trial_name,
            experiment_name=experiment_name,
            sagemaker_boto_client=sagemaker_boto_client,
        )
        if trial_components:
            for tc in trial_components:
                trial.add_trial_components(*trial_components)
        return trial

    @classmethod
    def list(
        cls,
        experiment_name=None,
        created_before=None,
        created_after=None,
        sort_by=None,
        sort_order=None,
        sagemaker_boto_client=None
    ):
        """
        List all trials matching the specified criteria.

        Args:
            experiment_name (str, optional): Name of the experiment. If specified, only trials in
                the experiment will be returned.
            created_before (datetime.datetime, optional): Return trials created before this instant.
            created_after (datetime.datetime, optional): Return trials created after this instant.
            sort_by (str, optional): Which property to sort results by. One of 'Name',
                'CreationTime'.
            sort_order (str, optional): One of 'Ascending', or 'Descending'.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.
        Returns:
            collections.Iterator[sagemaker.experiments.trial.TrialSummary]: An iterator over trials
                matching the specified criteria.
        """
        return super(Trial, cls)._list(
            "list_trials",
            api_types.TrialSummary.from_boto,
            "TrialSummaries",
            experiment_name=experiment_name,
            created_before=created_before,
            created_after=created_after,
            sort_by=sort_by,
            sort_order=sort_order,
            sagemaker_boto_client=sagemaker_boto_client,
        )

    def add_trial_component(self, tc):
        """Add the specified trial component to this trial."""
        if isinstance(tc, tracker.Tracker):
            trial_component_name = tc._trial_component.trial_component_name
        elif isinstance(tc, trial_component.TrialComponent):
            trial_component_name = tc.trial_component_name
        else:
            trial_component_name = str(tc)
        self.sagemaker_boto_client.associate_trial_component(
            TrialName=self.trial_name, TrialComponentName=trial_component_name)

    def remove_trial_component(self, tc):
        if isinstance(tc, tracker.Tracker):
            trial_component_name = tc._trial_component.trial_component_name
        elif isinstance(tc, trial_component.TrialComponent):
            trial_component_name = tc.trial_component_name
        else:
            trial_component_name = str(tc)
        self.sagemaker_boto_client.disassociate_trial_component(
            TrialName=self.trial_name, TrialComponentName=trial_component_name
        )

    def list_trial_components(self):
        """
        Returns all the trial components in this trial.
        Returns:
            collections.Iterator[sagemaker.experiments.trial_component.TrialComponentSummary]:  An iterator
                over trial component summaries.
        """
        return trial_component.TrialComponent.list(trial_name=self.trial_name,
                                                   sagemaker_boto_client=self.sagemaker_boto_client)
