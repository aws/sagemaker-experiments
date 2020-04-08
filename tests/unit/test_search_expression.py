from smexperiments.search_expression import Filter, Operator, NestedFilter, SearchExpression, BooleanOperator
import pytest


def test_filters():
    search_filter = Filter(name="learning_rate", operator=Operator.EQUALS, value="0.1")

    assert {"Name": "learning_rate", "Operator": "Equals", "Value": "0.1"} == search_filter.to_boto()


def test_partial_filters():
    search_filter = Filter(name="learning_rate")

    assert {"Name": "learning_rate"} == search_filter.to_boto()


def test_nested_filters():
    search_filter = Filter(name="learning_rate", operator=Operator.EQUALS, value="0.1")
    filters = [search_filter]
    nested_filters = NestedFilter(property_name="hyper_param", filters=filters)

    assert {
        "Filters": [{"Name": "learning_rate", "Operator": "Equals", "Value": "0.1"}],
        "NestedPropertyName": "hyper_param",
    } == nested_filters.to_boto()


def test_search_expression():
    search_filter = Filter(name="learning_rate", operator=Operator.EQUALS, value="0.1")
    nested_filter = NestedFilter(property_name="hyper_param", filters=[search_filter])
    search_expression = SearchExpression(
        filters=[search_filter],
        nested_filters=[nested_filter],
        sub_expressions=[],
        boolean_operator=BooleanOperator.AND,
    )

    assert {
        "Filters": [{"Name": "learning_rate", "Operator": "Equals", "Value": "0.1"}],
        "NestedFilters": [
            {
                "Filters": [{"Name": "learning_rate", "Operator": "Equals", "Value": "0.1"}],
                "NestedPropertyName": "hyper_param",
            }
        ],
        "SubExpressions": [],
        "Operator": "And",
    } == search_expression.to_boto()


def test_illegal_search_expression():
    with pytest.raises(ValueError, match="You must specify at least one subexpression, filter, or nested filter"):
        SearchExpression()
