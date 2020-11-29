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
"""Contains the SageMaker Training Job class."""
from smexperiments import _base_types, api_types


class TrainingJob(_base_types.Record):
    """Search for training jobs"""

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
        Search Training Job. Returns SearchResults in the account matching the search criteria.

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
        return super(TrainingJob, cls)._search(
            search_resource="TrainingJob",
            search_item_factory=api_types.TrainingJobSearchResult.from_boto,
            search_expression=None if search_expression is None else search_expression.to_boto(),
            sort_by=sort_by,
            sort_order=sort_order,
            max_results=max_results,
            sagemaker_boto_client=sagemaker_boto_client,
        )
