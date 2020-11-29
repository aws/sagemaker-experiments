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
from smexperiments.search_expression import Filter, Operator, SearchExpression, NestedFilter
from smexperiments.experiment import Experiment
import pytest


def test_search(sagemaker_boto_client):
    experiment_names_searched = []
    search_filter = Filter(name="ExperimentName", operator=Operator.CONTAINS, value="smexperiments-integ-")
    search_expression = SearchExpression(filters=[search_filter])
    for s in Experiment.search(
        search_expression=search_expression, max_results=10, sagemaker_boto_client=sagemaker_boto_client
    ):
        experiment_names_searched.append(s.experiment_name)

    assert len(experiment_names_searched) > 0
    assert experiment_names_searched  # sanity test


@pytest.mark.skip(reason="failed validation, need to wait for NestedFilter bug to be fixed")
def test_nested_search(sagemaker_boto_client):
    experiment_names_searched = []
    search_filter = Filter(name="ExperimentName", operator=Operator.CONTAINS, value="smexperiments-integ-")
    nested_filter = NestedFilter(property_name="ExperimentName", filters=[search_filter])
    search_expression = SearchExpression(nested_filters=[nested_filter])
    for s in Experiment.search(
        search_expression=search_expression, max_results=10, sagemaker_boto_client=sagemaker_boto_client
    ):
        experiment_names_searched.append(s.experiment_name)

    assert len(experiment_names_searched) > 0
    assert experiment_names_searched  # sanity test


def test_sub_expression(sagemaker_boto_client):
    experiment_names_searched = []
    search_filter = Filter(name="ExperimentName", operator=Operator.CONTAINS, value="smexperiments-integ-")
    sub_expression = SearchExpression(filters=[search_filter])
    search_expression = SearchExpression(sub_expressions=[sub_expression])
    for s in Experiment.search(
        search_expression=search_expression, max_results=10, sagemaker_boto_client=sagemaker_boto_client
    ):
        experiment_names_searched.append(s.experiment_name)

    assert len(experiment_names_searched) > 0
    assert experiment_names_searched  # sanity test
