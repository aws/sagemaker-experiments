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
"""Simplify Search Expression by provide a simplified DSL"""
from smexperiments._base_types import ApiObject
from enum import Enum, unique


@unique
class Operator(Enum):
    """Search operators"""

    EQUALS = "Equals"
    NOT_EQUALS = "NotEquals"
    GREATER_THAN = "GreaterThan"
    GREATER_THAN_OR_EQUAL = "GreaterThanOrEqualTo"
    LESS_THAN = "LessThan"
    LESS_THAN_OR_EQUAL = "LessThanOrEqualTo"
    CONTAINS = "Contains"
    EXISTS = "Exists"
    NOT_EXISTS = "NotExists"


@unique
class BooleanOperator(Enum):
    """Boolean search operation enum"""

    AND = "And"
    OR = "Or"


class SearchObject(ApiObject):
    """SearchObject"""

    def to_boto(self):
        """Convert a search object to boto"""
        return ApiObject.to_boto(self)


class Filter(SearchObject):
    """A Python class represent a Search Filter object."""

    name = None
    operator = None
    value = None

    def __init__(self, name, operator=None, value=None):
        """Construct a Filter object

        Args:
            name (str): filter field name
            operator (dict): one of Operator enum
            value (str): value of the field
        """
        self.name = name
        self.operator = None if operator is None else operator.value
        self.value = value


class NestedFilter(SearchObject):
    """A Python class represent a Nested Filter object."""

    nested_property_name = None
    filters = None

    def __init__(self, property_name, filters):
        """Construct a Nested Filter object

        Args:
            property_name (str): nested property name
            filters (list): list of Filter objects
        """
        self.nested_property_name = property_name
        self.filters = list(map(lambda x: x.to_boto(), filters))


class SearchExpression(SearchObject):
    """
    A Python class representation of a Search Expression object. A sample search expression defined in here:
    https://boto3.amazonaws.com/v1/documentation/api/1.12.8/reference/services/sagemaker.html#SageMaker.Client.search
    """

    filters = None
    nested_filters = None
    operator = None
    sub_expressions = None

    def __init__(self, filters=None, nested_filters=None, sub_expressions=None, boolean_operator=BooleanOperator.AND):
        """Construct a Search Expression object

        Args:
            filters (list): list of Filter objects
            nested_filters (list): list of Nested Filters objects
            sub_expressions (list): list of Search Expresssion objects
            boolean_operator (dict): one of the boolean operator enums
        """
        if filters is None and nested_filters is None and sub_expressions is None:
            raise ValueError("You must specify at least one subexpression, filter, or nested filter")
        self.filters = None if filters is None else list(map(lambda x: x.to_boto(), filters))
        self.nested_filters = None if nested_filters is None else list(map(lambda x: x.to_boto(), nested_filters))
        self.sub_expressions = None if sub_expressions is None else list(map(lambda x: x.to_boto(), sub_expressions))
        self.operator = boolean_operator.value
