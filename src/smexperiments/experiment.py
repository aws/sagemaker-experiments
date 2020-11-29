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
"""Contains the SageMaker Experiment class."""
from smexperiments import _base_types, api_types, trial, _utils, trial_component
import time


class Experiment(_base_types.Record):
    """
    An Amazon SageMaker experiment, which is a collection of related trials.

    New experiments are created by calling :meth:`~smexperiments.experiment.Experiment.create`. Existing
    experiments can be reloaded by calling :meth:`~smexperiments.experiment.Experiment.load`. You can
    add a new trial to an Experiment by calling :meth:`~smexperiments.experiment.Experiment.create_trial`.
    To remove an experiment and associated trials, trial components by calling :meth:`~smexperiments.experiment
    .Experiment.delete_all`.

    Examples:
        .. code-block:: python

            from smexperiments import experiment

            my_experiment = experiment.Experiment.create(experiment_name='AutoML')
            my_trial = my_experiment.create_trial(trial_name='random-forest')

            for exp in experiment.Experiment.list():
                print(exp)
            for trial in my_experiment.list_trials():
                print(trial)

            my_experiment.delete_all(action="--force")

    Attributes:
        experiment_name (str): The name of the experiment. The name must be unique within an account.
        description (str): A description of the experiment.
        tags (List[dict[str, str]]): A list of tags to associate with the experiment.
    """

    experiment_name = None
    description = None
    tags = None

    _boto_create_method = "create_experiment"
    _boto_load_method = "describe_experiment"
    _boto_update_method = "update_experiment"
    _boto_delete_method = "delete_experiment"

    _boto_update_members = ["experiment_name", "description", "display_name"]
    _boto_delete_members = ["experiment_name"]

    MAX_DELETE_ALL_ATTEMPTS = 3

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
        return self._invoke_api(self._boto_delete_method, self._boto_delete_members)

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
            cls._boto_load_method,
            experiment_name=experiment_name,
            sagemaker_boto_client=sagemaker_boto_client,
        )

    @classmethod
    def create(cls, experiment_name=None, description=None, tags=None, sagemaker_boto_client=None):
        """
        Create a new experiment in SageMaker and return an ``Experiment`` object.

        Args:
            experiment_name: (str): Name of the experiment. Must be unique. Required.
            experiment_description: (str, optional): Description of the experiment
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker. If not
                supplied, a default boto3 client will be created and used.
            tags (List[dict[str, str]]): A list of tags to associate with the experiment.

        Returns:
            sagemaker.experiments.experiment.Experiment: A SageMaker ``Experiment`` object
        """
        return cls._construct(
            cls._boto_create_method,
            experiment_name=experiment_name,
            description=description,
            tags=tags,
            sagemaker_boto_client=sagemaker_boto_client,
        )

    @classmethod
    def list(
        cls,
        created_before=None,
        created_after=None,
        sort_by=None,
        sort_order=None,
        sagemaker_boto_client=None,
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

    @classmethod
    def search(
        cls,
        search_expression=None,
        sort_by=None,
        sort_order=None,
        max_results=None,
        sagemaker_boto_client=None,
    ):
        """
        Search experiments. Returns SearchResults in the account matching the search criteria.

        Args:
            search_expression: (dict, optional): A Boolean conditional statement. Resource objects
                must satisfy this condition to be included in search results. You must provide at
                least one subexpression, filter, or nested filter.
            sort_by (str, optional): The name of the resource property used to sort the SearchResults.
                The default is LastModifiedTime
            sort_order (str, optional): How SearchResults are ordered. Valid values are Ascending or
                Descending . The default is Descending .
            max_results (int, optional): The maximum number of results to return in a SearchResponse.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker. If not
                supplied, a default boto3 client will be used.

        Returns:
            collections.Iterator[SearchResult] : An iterator over search results matching the search criteria.
        """
        return super(Experiment, cls)._search(
            search_resource="Experiment",
            search_item_factory=api_types.ExperimentSearchResult.from_boto,
            search_expression=None if search_expression is None else search_expression.to_boto(),
            sort_by=sort_by,
            sort_order=sort_order,
            max_results=max_results,
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

    def delete_all(self, action):
        """
        Force to delete the experiment and associated trials, trial components under the experiment.

        Args:
            action (str): pass in string '--force' to confirm recursively delete all the experiments, trials,
            and trial components.
        """
        if action != "--force":
            raise ValueError(
                "Must confirm with string '--force' in order to delete the experiment and "
                "associated trials, trial components."
            )

        delete_attempt_count = 0
        last_exception = None
        while True:
            if delete_attempt_count == self.MAX_DELETE_ALL_ATTEMPTS:
                raise Exception("Failed to delete, please try again.") from last_exception
            try:
                for trial_summary in self.list_trials():
                    t = trial.Trial.load(
                        sagemaker_boto_client=self.sagemaker_boto_client, trial_name=trial_summary.trial_name
                    )
                    for trial_component_summary in t.list_trial_components():
                        tc = trial_component.TrialComponent.load(
                            sagemaker_boto_client=self.sagemaker_boto_client,
                            trial_component_name=trial_component_summary.trial_component_name,
                        )
                        tc.delete(force_disassociate=True)
                        # to prevent throttling
                        time.sleep(1.2)
                    t.delete()
                    # to prevent throttling
                    time.sleep(1.2)
                self.delete()
                break
            except Exception as ex:
                last_exception = ex
            finally:
                delete_attempt_count = delete_attempt_count + 1
