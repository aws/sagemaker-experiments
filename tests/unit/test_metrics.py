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
import time

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
    return os.path.join(tempdir, "foo.json")


@pytest.fixture
def resource_arn():
    return "arn:1234"


@pytest.fixture
def timestamp():
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)


def test_RawMetricData_utc_timestamp():
    utcnow = datetime.datetime.now(datetime.timezone.utc)
    assert utcnow.tzinfo
    metric = metrics._RawMetricData(metric_name="foo", value=1.0, timestamp=utcnow)
    assert utcnow.timestamp() == metric.Timestamp


def test_RawMetricData_aware_timestamp():
    aware_datetime = datetime.datetime.now(dateutil.tz.gettz("America/Chicago"))
    assert aware_datetime.tzinfo
    metric = metrics._RawMetricData(metric_name="foo", value=1.0, timestamp=aware_datetime)
    assert (aware_datetime - aware_datetime.utcoffset()).replace(
        tzinfo=datetime.timezone.utc
    ).timestamp() == metric.Timestamp


def test_RawMetricData_naive_timestamp():
    naive_datetime = datetime.datetime.now()
    assert naive_datetime.tzinfo is None
    metric = metrics._RawMetricData(metric_name="foo", value=1.0, timestamp=naive_datetime)
    local_datetime = naive_datetime.replace(tzinfo=dateutil.tz.tzlocal())
    assert (local_datetime - local_datetime.utcoffset()).replace(
        tzinfo=datetime.timezone.utc
    ).timestamp() == metric.Timestamp


def test_RawMetricData_number_timestamp():
    time_now = time.time()
    metric = metrics._RawMetricData(metric_name="foo", value=1.0, timestamp=time_now)
    assert time_now == metric.Timestamp


def test_RawMetricData_invalid_timestamp():
    with pytest.raises(ValueError):
        metrics._RawMetricData(metric_name="IFail", value=100, timestamp=time.time() - 2000000)
    with pytest.raises(ValueError):
        metrics._RawMetricData(metric_name="IFail", value=100, timestamp=time.time() + 10000)


def test_file_metrics_writer_log_metric(timestamp, filepath):
    now = datetime.datetime.now(datetime.timezone.utc)
    writer = metrics.SageMakerFileMetricsWriter(filepath)
    writer.log_metric(metric_name="foo", value=1.0)
    writer.log_metric(metric_name="foo", value=2.0, iteration_number=1)
    writer.log_metric(metric_name="foo", value=3.0, timestamp=timestamp)
    writer.log_metric(metric_name="foo", value=4.0, timestamp=timestamp, iteration_number=2)
    writer.close()

    lines = [x for x in open(filepath).read().split("\n") if x]
    [entry_one, entry_two, entry_three, entry_four] = [json.loads(line) for line in lines]

    assert "foo" == entry_one["MetricName"]
    assert 1.0 == entry_one["Value"]
    assert (now.timestamp() - entry_one["Timestamp"]) < 1
    assert "IterationNumber" not in entry_one

    assert 1 == entry_two["IterationNumber"]
    assert timestamp.timestamp() == entry_three["Timestamp"]
    assert 2 == entry_four["IterationNumber"]


def test_file_metrics_writer_flushes_buffer_every_line_log_metric(filepath):
    writer = metrics.SageMakerFileMetricsWriter(filepath)

    writer.log_metric(metric_name="foo", value=1.0)

    lines = [x for x in open(filepath).read().split("\n") if x]
    [entry_one] = [json.loads(line) for line in lines]
    assert "foo" == entry_one["MetricName"]
    assert 1.0 == entry_one["Value"]

    writer.log_metric(metric_name="bar", value=2.0)
    lines = [x for x in open(filepath).read().split("\n") if x]
    [entry_one, entry_two] = [json.loads(line) for line in lines]
    assert "bar" == entry_two["MetricName"]
    assert 2.0 == entry_two["Value"]

    writer.log_metric(metric_name="biz", value=3.0)
    lines = [x for x in open(filepath).read().split("\n") if x]
    [entry_one, entry_two, entry_three] = [json.loads(line) for line in lines]
    assert "biz" == entry_three["MetricName"]
    assert 3.0 == entry_three["Value"]

    writer.close()


def test_file_metrics_writer_context_manager(timestamp, filepath):
    with metrics.SageMakerFileMetricsWriter(filepath) as writer:
        writer.log_metric("foo", value=1.0, timestamp=timestamp)
    entry = json.loads(open(filepath, "r").read().strip())
    assert {"MetricName": "foo", "Value": 1.0, "Timestamp": timestamp.timestamp()}.items() <= entry.items()


def test_file_metrics_writer_fail_write_on_close(filepath):
    writer = metrics.SageMakerFileMetricsWriter(filepath)
    writer.log_metric(metric_name="foo", value=1.0)
    writer.close()
    with pytest.raises(metrics.SageMakerMetricsWriterException):
        writer.log_metric(metric_name="foo", value=1.0)


def test_file_metrics_writer_no_write(filepath):
    writer = metrics.SageMakerFileMetricsWriter(filepath)
    writer.close()
    assert not os.path.exists(filepath)
