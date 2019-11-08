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
import os
import pytest
import tempfile
import shutil
import datetime
import dateutil
import json
from smexperiments import metrics
import unittest.mock


@pytest.fixture
def tempdir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)


@pytest.fixture
def sagemaker_boto_client():
    return unittest.mock.Mock()


@pytest.fixture
def filepath(tempdir):
    return os.path.join(tempdir, 'foo.json')


@pytest.fixture
def resource_arn():
    return 'arn:1234'


@pytest.fixture
def timestamp():
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)


def test_RawMetricData_utc_timestamp():
    utcnow = datetime.datetime.now(datetime.timezone.utc)
    assert utcnow.tzinfo
    metric = metrics._RawMetricData(metric_name='foo', value=1.0, timestamp=utcnow)
    assert utcnow == metric.Timestamp


def test_RawMetricData_aware_timestamp():
    aware_datetime = datetime.datetime(2000, 1, 1, tzinfo=dateutil.tz.gettz('America/Chicago'))
    assert aware_datetime.tzinfo
    metric = metrics._RawMetricData(metric_name='foo', value=1.0, timestamp=aware_datetime)
    assert (aware_datetime - aware_datetime.utcoffset()).replace(tzinfo=datetime.timezone.utc) == metric.Timestamp


def test_RawMetricData_naive_timestamp():
    naive_datetime = datetime.datetime(2000, 1, 1)
    assert naive_datetime.tzinfo is None
    metric = metrics._RawMetricData(metric_name='foo', value=1.0, timestamp=naive_datetime)
    local_datetime = naive_datetime.replace(tzinfo=dateutil.tz.tzlocal())
    assert (local_datetime - local_datetime.utcoffset()).replace(tzinfo=datetime.timezone.utc) == metric.Timestamp


def test_RawMetricData_number_timestamp():
    metric = metrics._RawMetricData(metric_name='foo', value=1.0, timestamp=371730600)
    assert metric.Timestamp == datetime.datetime(1981, 10, 12, 10, 30, tzinfo=datetime.timezone.utc)


def test_file_metrics_writer_log_metric(timestamp, filepath):
    now = datetime.datetime.utcnow()
    writer = metrics.SageMakerFileMetricsWriter(filepath)
    writer.log_metric(metric_name='foo', value=1.0)
    writer.log_metric(metric_name='foo', value=2.0, iteration_number=1)
    writer.log_metric(metric_name='foo', value=3.0, timestamp=timestamp)
    writer.log_metric(metric_name='foo', value=4.0, timestamp=timestamp, iteration_number=2)
    writer.close()

    lines = [x for x in open(filepath).read().split('\n') if x]
    [entry_one, entry_two, entry_three, entry_four] = [json.loads (line) for line in lines]

    assert 'foo' == entry_one['MetricName']
    assert 1.0 == entry_one['Value']
    assert (now.timestamp() - entry_one['Timestamp']) < 1
    assert 'IterationNumber' not in entry_one

    assert 1 == entry_two['IterationNumber']
    assert timestamp.timestamp() == entry_three['Timestamp']
    assert 2 == entry_four['IterationNumber']


def test_file_metrics_writer_context_manager(timestamp, filepath):
    with metrics.SageMakerFileMetricsWriter(filepath) as writer:
        writer.log_metric('foo', value=1.0, timestamp=timestamp)
    entry = json.loads(open(filepath, 'r').read().strip())
    assert {
        'MetricName': 'foo',
        'Value': 1.0,
        'Timestamp': timestamp.timestamp()
    }.items() <= entry.items()


def test_file_metrics_writer_fail_write_on_close(filepath):
    writer = metrics.SageMakerFileMetricsWriter(filepath)
    writer.log_metric(metric_name='foo', value=1.0)
    writer.close()
    with pytest.raises(metrics.SageMakerMetricsWriterException):
        writer.log_metric(metric_name='foo', value=1.0)


def test_file_metrics_writer_no_write(filepath):
    writer = metrics.SageMakerFileMetricsWriter(filepath)
    writer.close()
    assert not os.path.exists(filepath)


@unittest.mock.patch('time.sleep')
def test_api_metrics_writer_log_metric(patched_time_sleep, resource_arn, timestamp, sagemaker_boto_client):

    now = datetime.datetime.utcnow()
    writer = metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client)
    writer.log_metric(metric_name='foo', value=1.0)
    writer.log_metric(metric_name='foo', value=2.0, iteration_number=1)
    writer.log_metric(metric_name='foo', value=3.0, timestamp=timestamp)
    writer.log_metric(metric_name='foo', value=4.0, timestamp=timestamp, iteration_number=2)
    writer.close()

    submitted_data = []
    for _, _, call_kwargs in sagemaker_boto_client.batch_put_metrics.mock_calls:
        submitted_data += call_kwargs['MetricData']

    [entry_one, entry_two, entry_three, entry_four] = submitted_data

    assert 'foo' == entry_one['MetricName']
    assert 1.0 == entry_one['Value']
    assert (now - entry_one['Timestamp']) < datetime.timedelta(seconds=1)
    assert 'IterationNumber' not in entry_one

    assert 1 == entry_two['IterationNumber']
    assert timestamp == entry_three['Timestamp']
    assert 2 == entry_four['IterationNumber']


def test_api_metrics_writer_context_manager(timestamp, sagemaker_boto_client, resource_arn):
    with metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client) as writer:
        writer.log_metric('foo', value=1.0, timestamp=timestamp)
    _ ,_, kwargs = sagemaker_boto_client.batch_put_metrics.mock_calls[0]
    [entry]= kwargs['MetricData']
    assert {
        'MetricName': 'foo',
        'Value': 1.0,
        'Timestamp': timestamp
    }.items() <= entry.items()


def test_api_metrics_writer_fail_write_on_close(sagemaker_boto_client, resource_arn):
    writer = metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client)
    writer.log_metric(metric_name='foo', value=1.0)
    writer.close()
    with pytest.raises(metrics.SageMakerMetricsWriterException):
        writer.log_metric(metric_name='foo', value=1.0)


def test_api_metrics_writer_no_write(sagemaker_boto_client, resource_arn):
    writer = metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client)
    writer.close()


def test_api_metrics_writer_put_fails(sagemaker_boto_client, resource_arn):
    sagemaker_boto_client.batch_put_metrics.side_effect = ValueError('Boo!')

    writer = metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client, raise_on_close=True)
    writer.log_metric('foo', 1.0)
    with pytest.raises(ValueError) as error:
        writer.close()
        assert ValueError('Boo!') == error


def test_api_metrics_writer_put_returns_errors(timestamp, sagemaker_boto_client, resource_arn):
    sagemaker_boto_client.batch_put_metrics.return_value = {
        'Errors': [
            {
                'Code': 'InternalError',
                'Message': 'Bah',
                'MetricIndex': 0
            }
        ]
    }
    writer = metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client, raise_on_close=True)
    writer.log_metric('foo', 1.0, timestamp=timestamp)
    with pytest.raises(metrics.SageMakerMetricsWriterException) as ex:
        writer.close()
        [error] = ex.value.errors

        assert 'InternalError' == error.code
        assert 'Bah' == error.message
        assert 0 == error.metric_index
        assert {
            'MetricName': 'foo',
            'Value': 1.0,
            'Timestamp': timestamp
        } == error.metric_value
