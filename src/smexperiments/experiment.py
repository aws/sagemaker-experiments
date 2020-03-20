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

"""Contains the SageMaker Experiment class."""
from smexperiments import _base_types, api_types, trial, _utils


class Experiment(_base_types.Record):
    """
    An Amazon SageMaker experiment, which is a collection of related trials.

    New experiments are created by calling :meth:`~smexperiments.experiment.Experiment.create`. Existing
    experiments can be reloaded by calling :meth:`~smexperiments.experiment.Experiment.load`. You can
    add a new trial to an Experiment by calling :meth:`~smexperiments.experiment.Experiment.create_trial`.
    To remove a Trial from an experiment, delete the trial.

    Examples:
        .. code-block:: python

            from smexperiments import experiment

            my_experiment = experiment.Experiment.create(experiment_name='AutoML')
            my_trial = my_experiment.create_trial(trial_name='random-forest')

            for exp in experiment.Experiment.list():
                print(exp)
            for trial in my_experiment.list_trials():
                print(trial)

            my_trial.delete()
            my_experiment.delete()

    Attributes:
        experiment_name (str): The name of the experiment. The name must be unique within an account.
        description (str): A description of the experiment.
    """

    experiment_name = None
    description = None

    _boto_create_method = "create_experiment"
    _boto_load_method = "describe_experiment"
    _boto_update_method = "update_experiment"
    _boto_delete_method = "delete_experiment"

    _boto_update_members = ["experiment_name", "description", "display_name"]
    _boto_delete_members = ["experiment_name"]

    def save(self):
        """Save the state of this Experiment to SageMaker.

        Returns:
            dict: Update experiment API response.
        """
        return self._invoke_api(self._boto_update_method, self._boto_update_members)

    def delete(self):
        """Delete this Experiment from SageMaker.

        Deleting an Experiment requires that each Trial in the Experiment is first deleted.

        Returns:
            dict: Delete experiment API response.
        """
        self._invoke_api(self._boto_delete_method, self._boto_delete_members)

    @classmethod
    def load(cls, experiment_name, sagemaker_boto_client=None):
        """
        Load an existing experiment and return an ``Experiment`` object representing it.

        Args:
            experiment_name: (str): Name of the experiment
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.

        Returns:
            sagemaker.experiments.experiment.Experiment: A SageMaker ``Experiment`` object
        """
        return cls._construct(
            cls._boto_load_method, experiment_name=experiment_name, sagemaker_boto_client=sagemaker_boto_client,
        )

    @classmethod
    def create(cls, experiment_name=None, description=None, sagemaker_boto_client=None):
        """
        Create a new experiment in SageMaker and return an ``Experiment`` object.

        Args:
            experiment_name: (str): Name of the experiment. Must be unique. Required.
            experiment_description: (str, optional): Description of the experiment
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker. If not
                supplied, a default boto3 client will be created and used.

        Returns:
            sagemaker.experiments.experiment.Experiment: A SageMaker ``Experiment`` object
        """
        return cls._construct(
            cls._boto_create_method,
            experiment_name=experiment_name,
            description=description,
            sagemaker_boto_client=sagemaker_boto_client,
        )

    @classmethod
    def list(
        cls, created_before=None, created_after=None, sort_by=None, sort_order=None, sagemaker_boto_client=None,
    ):
        """
        List experiments. Returns experiments in the account matching the specified criteria.

        Args:
            created_before: (datetime.datetime, optional): Return experiments created before this
                instant.
            created_after: (datetime.datetime, optional): Return experiments created after this
                instant.
            sort_by (str, optional): Which property to sort results by. One of
                'Name', 'CreationTime'.
            sort_order (str, optional): One of 'Ascending', or 'Descending'.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker. If not
                supplied, a default boto3 client will be used.

        Returns:
            collections.Iterator[sagemaker.experiments.api_types.ExperimentSummary] : An iterator
                over experiment summaries matching the specified criteria.
        """
        return super(Experiment, cls)._list(
            "list_experiments",
            api_types.ExperimentSummary.from_boto,
            "ExperimentSummaries",
            created_before=created_before,
            created_after=created_after,
            sort_by=sort_by,
            sort_order=sort_order,
            sagemaker_boto_client=sagemaker_boto_client,
        )

    def list_trials(self, created_before=None, created_after=None, sort_by=None, sort_order=None):
        """List trials in this experiment matching the specified criteria.

        Args:
            created_before (datetime.datetime, optional): Return trials created before this instant.
            created_after (datetime.datetime, optional): Return trials created after this instant.
            sort_by (str, optional): Which property to sort results by. One of 'Name',
                'CreationTime'.
            sort_order (str, optional): One of 'Ascending', or 'Descending'.

        Returns:
            collections.Iterator[sagemaker.experiments.api_types.TrialSummary] : An iterator over
                trials matching the criteria.
        """
        return trial.Trial.list(
            experiment_name=self.experiment_name,
            created_before=created_before,
            created_after=created_after,
            sort_by=sort_by,
            sort_order=sort_order,
            sagemaker_boto_client=self.sagemaker_boto_client,
        )

    def create_trial(self, trial_name=None, trial_name_prefix="SageMakerTrial"):
        """Create a trial in this experiment.

        Since trial names are expected to be unique in an account, ``trial_name_prefix`` can be provided
        instead of ``trial_name``. In this case a unique name will be generated that begins with the specified
        prefix.

        Args:
            trial_name (str): Name of the trial.
            trial_name_prefix (str): Prefix for the trial name if you want SageMaker to
                auto-generate the trial name.

        Returns:
            sagemaker.experiments.trial.Trial : A SageMaker ``Trial`` object representing the
                created trial.
        """
        if not trial_name:
            trial_name = _utils.name(trial_name_prefix)
        return trial.Trial.create(
            trial_name=trial_name,
            experiment_name=self.experiment_name,
            sagemaker_boto_client=self.sagemaker_boto_client,
        )
