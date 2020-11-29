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
"""Contains the Trial class."""

from smexperiments import api_types, _base_types, trial_component, _utils, tracker
import time


class Trial(_base_types.Record):
    """
    An execution of a data-science workflow with an experiment.

    Consists of a list of trial component objects, which document individual activities within the workflow.

    Examples:
        .. code-block:: python

            from smexperiments import trial, experiment, tracker

            my_experiment = experiment.Experiment.create(experiment_name='AutoML')
            my_trial = trial.Trial.create('AutoML')

            my_tracker = tracker.Tracker.create()
            # log hyper parameter of learning rate
            my_tracker.log_parameter('learning_rate', 0.01)
            my_trial.add_trial_component(my_tracker)

            for trial_component in my_trial.list_trial_components():
                print(trial_component)

            my_trial.remove_trial_component(my_tracker)
            my_trial.delete()

    Attributes:
        trial_name (str): The name of the trial.
        experiment_name (str): The name of the trial's experiment.
        tags (List[dict[str, str]]): A list of tags to associate with the trial.
    """

    trial_name = None
    experiment_name = None
    tags = None

    _boto_create_method = "create_trial"
    _boto_load_method = "describe_trial"
    _boto_delete_method = "delete_trial"
    _boto_update_method = "update_trial"

    _boto_update_members = ["trial_name", "display_name"]
    _boto_delete_members = ["trial_name"]

    MAX_DELETE_ALL_ATTEMPTS = 3

    @classmethod
    def _boto_ignore(cls):
        return super(Trial, cls)._boto_ignore() + ["CreatedBy"]

    def save(self):
        """Save the state of this Trial to SageMaker.

        Returns:
            dict: Update trial response.
        """
        return self._invoke_api(self._boto_update_method, self._boto_update_members)

    def delete(self):
        """Delete this Trial from SageMaker.

        Requires that this Trial contains no TrialComponents. Individual TrialComponents can be removed by
        calling :meth:`~smexperiments.trial.Trial.remove_trial_component`.

         Returns:
            dict: Delete trial response.
        """
        return self._invoke_api(self._boto_delete_method, self._boto_delete_members)

    @classmethod
    def load(cls, trial_name, sagemaker_boto_client=None):
        """Load an existing trial and return a ``Trial`` object.

        Args:
            trial_name: (str): Name of the Trial.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.

        Returns:
            smexperiments.trial.Trial: A SageMaker ``Trial`` object
        """
        return super(Trial, cls)._construct(
            cls._boto_load_method, trial_name=trial_name, sagemaker_boto_client=sagemaker_boto_client
        )

    @classmethod
    def create(cls, experiment_name, trial_name=None, sagemaker_boto_client=None, trial_components=None, tags=None):
        """Create a new trial and return a ``Trial`` object.

        Args:
            experiment_name: (str): Name of the experiment to create this trial in.
            trial_name: (str, optional): Name of the Trial. If not specified, an auto-generated name will be used.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.
            trial_components (list): A list of trial component names, trial components, or trial component trackers.
            tags (List[dict[str, str]]): A list of tags to associate with the trial.

        Returns:
            smexperiments.trial.Trial: A SageMaker ``Trial`` object
        """
        trial_name = trial_name or _utils.name("Trial")
        trial = super(Trial, cls)._construct(
            cls._boto_create_method,
            trial_name=trial_name,
            experiment_name=experiment_name,
            tags=tags,
            sagemaker_boto_client=sagemaker_boto_client,
        )
        if trial_components:
            for tc in trial_components:
                trial.add_trial_component(tc)
        return trial

    @classmethod
    def list(
        cls,
        experiment_name=None,
        trial_component_name=None,
        created_before=None,
        created_after=None,
        sort_by=None,
        sort_order=None,
        sagemaker_boto_client=None,
    ):
        """List all trials matching the specified criteria.

        Args:
            experiment_name (str, optional): Name of the experiment. If specified, only trials in
                the experiment will be returned.
            trial_component_name (str, optional): Name of the trial component. If specified, only
                trials with this trial component name will be returned.
            created_before (datetime.datetime, optional): Return trials created before this instant.
            created_after (datetime.datetime, optional): Return trials created after this instant.
            sort_by (str, optional): Which property to sort results by. One of 'Name',
                'CreationTime'.
            sort_order (str, optional): One of 'Ascending', or 'Descending'.
            sagemaker_boto_client (SageMaker.Client, optional): Boto3 client for SageMaker.
                If not supplied, a default boto3 client will be created and used.

        Returns:
            collections.Iterator[smexperiments.trial.TrialSummary]: An iterator over trials
                matching the specified criteria.
        """
        return super(Trial, cls)._list(
            "list_trials",
            api_types.TrialSummary.from_boto,
            "TrialSummaries",
            experiment_name=experiment_name,
            trial_component_name=trial_component_name,
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
        return super(Trial, cls)._search(
            search_resource="ExperimentTrial",
            search_item_factory=api_types.TrialSearchResult.from_boto,
            search_expression=None if search_expression is None else search_expression.to_boto(),
            sort_by=sort_by,
            sort_order=sort_order,
            max_results=max_results,
            sagemaker_boto_client=sagemaker_boto_client,
        )

    def add_trial_component(self, tc):
        """Add the specified trial component to this ``Trial``.

        A trial component may belong to many trials and a trial may have many trial components.

        Args:
           tc (str or Tracker or TrialComponent or TrialComponentSummary): The trial component to
           add. Can be one of a Tracker instance, a TrialComponent instance, or a string containing
           the name of the trial component to add.
        """
        if isinstance(tc, tracker.Tracker):
            trial_component_name = tc.trial_component.trial_component_name
        elif isinstance(tc, trial_component.TrialComponent):
            trial_component_name = tc.trial_component_name
        elif isinstance(tc, api_types.TrialComponentSummary):
            trial_component_name = tc.trial_component_name
        else:
            trial_component_name = str(tc)
        self.sagemaker_boto_client.associate_trial_component(
            TrialName=self.trial_name, TrialComponentName=trial_component_name
        )

    def remove_trial_component(self, tc):
        """Remove the specified trial component from this trial.

        Args:
            tc (str or Tracker or TrialComponent or TrialComponentSummary): The trial component to
            remove. Can be one of a Tracker instance, a TrialComponent instance, or a string
            containing the name of the trial component to remove.
        """
        if isinstance(tc, tracker.Tracker):
            trial_component_name = tc.trial_component.trial_component_name
        elif isinstance(tc, trial_component.TrialComponent):
            trial_component_name = tc.trial_component_name
        elif isinstance(tc, api_types.TrialComponentSummary):
            trial_component_name = tc.trial_component_name
        else:
            trial_component_name = str(tc)
        self.sagemaker_boto_client.disassociate_trial_component(
            TrialName=self.trial_name, TrialComponentName=trial_component_name
        )

    def list_trial_components(
        self, created_before=None, created_after=None, sort_by=None, sort_order=None, max_results=None, next_token=None
    ):
        """List trial components in this trial matching the specified criteria.

        Args:
            created_before (datetime.datetime, optional): Return trials created before this instant.
            created_after (datetime.datetime, optional): Return trials created after this instant.
            sort_by (str, optional): Which property to sort results by. One of 'Name',
                'CreationTime'.
            sort_order (str, optional): One of 'Ascending', or 'Descending'.
            max_results (int, optional): maximum number of trial components to retrieve
            next_token (str, optional): token for next page of results

        Returns:
            collections.Iterator[smexperiments.api_types.TrialComponentSummary] : An iterator over
                trials matching the criteria.
        """
        return trial_component.TrialComponent.list(
            trial_name=self.trial_name,
            created_before=created_before,
            created_after=created_after,
            sort_by=sort_by,
            sort_order=sort_order,
            max_results=max_results,
            next_token=next_token,
            sagemaker_boto_client=self.sagemaker_boto_client,
        )

    def delete_all(self, action):
        """
        Force to delete the trial and associated trial components under.

        Args:
            action (str): pass in string '--force' to confirm delete the trial and all associated trial components.
        """
        if action != "--force":
            raise ValueError(
                "Must confirm with string '--force' in order to delete the trial and " "associated trial components."
            )

        delete_attempt_count = 0
        last_exception = None
        while True:
            if delete_attempt_count == self.MAX_DELETE_ALL_ATTEMPTS:
                raise Exception("Failed to delete, please try again.") from last_exception
            try:
                for trial_component_summary in self.list_trial_components():
                    tc = trial_component.TrialComponent.load(
                        sagemaker_boto_client=self.sagemaker_boto_client,
                        trial_component_name=trial_component_summary.trial_component_name,
                    )
                    tc.delete(force_disassociate=True)
                    # to prevent throttling
                    time.sleep(1.2)
                self.delete()
                break
            except Exception as ex:
                last_exception = ex
            finally:
                delete_attempt_count = delete_attempt_count + 1
