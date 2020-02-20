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
import pytest
import unittest.mock

from smexperiments import _base_types


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


def test_from_boto():
    obj = _base_types.ApiObject.from_boto(dict(A=10))
    assert obj.a == 10


def test_to_boto():
    assert dict(A=10) == _base_types.ApiObject.to_boto({"a": 10})


def test_custom_type():
    class TestTypeA(_base_types.ApiObject):
        pass

    class TestTypeB(_base_types.ApiObject):
        _custom_boto_types = {"test_type_a_value": (TestTypeA, False)}

    obj = TestTypeB.from_boto(dict(TestTypeAValue=dict(SomeValue=10)))

    assert obj.test_type_a_value == TestTypeA(some_value=10)

    obj2 = TestTypeB(test_type_a_value=TestTypeA(some_value=10))
    assert TestTypeB.to_boto(vars(obj2)) == dict(TestTypeAValue=dict(SomeValue=10))


def test_custom_type_list():
    class TestTypeA(_base_types.ApiObject):
        pass

    class TestTypeB(_base_types.ApiObject):
        _custom_boto_types = {"test_type_a_value": (TestTypeA, True)}

    obj = TestTypeB.from_boto(dict(TestTypeAValue=[dict(SomeValue=10), dict(SomeValue=11)]))

    assert obj.test_type_a_value == [TestTypeA(some_value=10), TestTypeA(some_value=11)]
    assert dict(TestTypeAValue=[dict(SomeValue=10), dict(SomeValue=11)]) == TestTypeB.to_boto(vars(obj))


class DummyRecordSummary(_base_types.ApiObject):
    pass


class DummyRecord(_base_types.Record):

    _boto_create_method = "create"
    _boto_update_method = "update"
    _boto_delete_method = "delete"

    _boto_update_members = ["a"]
    _boto_delete_members = ["a", "b"]

    def update(self):
        """Placeholder docstring"""
        return self._invoke_api(self._boto_update_method, self._boto_update_members)

    def delete(self):
        """Placeholder docstring"""
        self._invoke_api(self._boto_delete_method, self._boto_delete_members)


def test_custom_type_dict():
    class TestTypeA(_base_types.ApiObject):
        pass

    class TestTypeB(_base_types.ApiObject):
        _custom_boto_types = {"test_type_a_value": (TestTypeA, True)}

    obj = TestTypeB.from_boto(dict(TestTypeAValue={"key_1": dict(SomeValue=10), "key_2": dict(SomeValue=11)}))

    assert obj.test_type_a_value == {
        "key_1": TestTypeA(some_value=10),
        "key_2": TestTypeA(some_value=11),
    }
    assert dict(TestTypeAValue={"key_1": dict(SomeValue=10), "key_2": dict(SomeValue=11)}) == TestTypeB.to_boto(
        vars(obj)
    )


def test_construct(sagemaker_boto_client):
    sagemaker_boto_client.create.return_value = dict(C=20)
    record = DummyRecord._construct(DummyRecord._boto_create_method, sagemaker_boto_client, a=10, b=10)

    assert record.a == 10
    assert record.b == 10
    assert record.c == 20


def test_update(sagemaker_boto_client):
    sagemaker_boto_client.update.return_value = {}
    record = DummyRecord(sagemaker_boto_client, a=10, b=10)
    record.update()
    sagemaker_boto_client.update.assert_called_with(A=10)


def test_delete(sagemaker_boto_client):
    sagemaker_boto_client.delete.return_value = {}
    record = DummyRecord(sagemaker_boto_client, a=10, b=10)
    record.delete()
    sagemaker_boto_client.delete.assert_called_with(A=10, B=10)


def test_list_empty(sagemaker_boto_client):
    sagemaker_boto_client.list.return_value = {"TestRecordSummaries": []}
    assert [] == list(
        DummyRecord._list(
            "list", DummyRecordSummary.from_boto, "TestRecordSummaries", sagemaker_boto_client=sagemaker_boto_client,
        )
    )


def test_list_with_items(sagemaker_boto_client):
    sagemaker_boto_client.list.return_value = {"TestRecordSummaries": [{"Foo": "bar"}]}
    assert [DummyRecordSummary(foo="bar")] == list(
        DummyRecord._list(
            "list", DummyRecordSummary.from_boto, "TestRecordSummaries", sagemaker_boto_client=sagemaker_boto_client,
        )
    )


def test_list_with_next_token(sagemaker_boto_client):
    sagemaker_boto_client.list.side_effect = [
        {"TestRecordSummaries": [{"A": 1}, {"A": 2}], "NextToken": "a"},
        {"TestRecordSummaries": [{"A": 3}, {"A": 4}], "NextToken": None},
    ]

    assert [DummyRecordSummary(a=i) for i in range(1, 5)] == list(
        DummyRecord._list(
            "list", DummyRecordSummary.from_boto, "TestRecordSummaries", sagemaker_boto_client=sagemaker_boto_client,
        )
    )


@unittest.mock.patch("smexperiments._base_types._utils.sagemaker_client")
def test_list_no_client(mocked_utils_sagemaker_client, sagemaker_boto_client):
    mocked_utils_sagemaker_client.return_value = sagemaker_boto_client
    sagemaker_boto_client.list.side_effect = []
    list(DummyRecord._list("list", DummyRecordSummary.from_boto, "TestRecordSummaries"))
    _base_types._utils.sagemaker_client.assert_called()
