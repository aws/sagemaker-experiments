from smexperiments import api_types


def test_parameter_str_string():
    param = api_types.TrialComponentParameterValue('kmeans', None)

    param_str = str(param)

    assert 'kmeans' == param_str


def test_parameter_str_number():
    param = api_types.TrialComponentParameterValue(None, 2.99792458)

    param_str = str(param)

    assert '2.99792458' == param_str


def test_parameter_str_none():
    param = api_types.TrialComponentParameterValue(None, None)

    param_str = str(param)

    assert '' == param_str
