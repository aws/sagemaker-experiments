# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#   http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from smexperiments import api_types


def test_parameter_str_string():
    param = api_types.TrialComponentParameterValue("kmeans", None)

    param_str = str(param)

    assert "kmeans" == param_str


def test_parameter_str_number():
    param = api_types.TrialComponentParameterValue(None, 2.99792458)

    param_str = str(param)

    assert "2.99792458" == param_str


def test_parameter_str_none():
    param = api_types.TrialComponentParameterValue(None, None)

    param_str = str(param)

    assert "" == param_str
