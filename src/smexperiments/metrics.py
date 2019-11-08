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
import datetime
import json
import os
import queue
import threading
import time

import boto3
import dateutil.tz

from smexperiments import api_types

METRICS_DIR = os.environ.get('SAGEMAKER_METRICS_DIRECTORY', '.')


class SageMakerFileMetricsWriter(object):

    def __init__(self, metrics_file_path=None):
        self._metrics_file_path = metrics_file_path
        self._file = None
        self._closed = False

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        self._write_metric_value(
            _RawMetricData(
                metric_name=metric_name, value=value, timestamp=timestamp, iteration_number=iteration_number,
                record_type='File')
        )

    def close(self):
        if not self._closed and self._file:
            self._file.close()
            self._file = None  # invalidate reference, causing subsequent log_metric to fail.
        self._closed = True

    def __enter__(self):
        """Return self"""
        return self

    def __exit__(self, type, value, traceback):
        """Execute self.close()"""
        self.close()

    def __del__(self):
        """Execute self.close()"""
        self.close()

    def _get_metrics_file_path(self):
        pid_filename = '{}.json'.format(str(os.getpid()))
        return self._metrics_file_path or os.path.join(METRICS_DIR, pid_filename)

    def _write_metric_value(self, raw_metric_data):
        try:
            self._file.write(json.dumps(raw_metric_data.to_record()))
            self._file.write('\n')
        except AttributeError:
            if self._closed:
                raise SageMakerMetricsWriterException('log_metric called on a closed writer')
            elif not self._file:
                self._file = open(self._get_metrics_file_path(), 'a')
                self._file.write(json.dumps(raw_metric_data.to_record()))
                self._file.write('\n')
            else:
                raise


class SageMakerMetricsWriterException(Exception):

    def __init__(self, message, errors=None):
        self.message = message
        if errors:
            self.errors = errors


class SageMakerMetricsWriter(object):

    BATCH_MAX_SIZE = 10
    QUEUE_SIZE = 3 * BATCH_MAX_SIZE
    MIN_PUBLISH_INTERVAL_SECONDS = 1

    # A poison pill used to kill the publisher thread.
    _terminate_message = 666101999

    def __init__(self, resource_arn, sagemaker_boto_client=None, raise_on_close=False):
        self._resource_arn = resource_arn
        self._sagemaker_boto_client = sagemaker_boto_client or boto3.Session().client('sagemaker')
        self.raise_on_close = raise_on_close
        self._publisher_thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._work_queue = queue.Queue(maxsize=self.QUEUE_SIZE)
        self._last_exception = None
        self._publisher_thread.start()
        self._should_terminate = False
        self._closed = False

    def _publish_loop(self):
        while True:
            self._publish_metrics()
            if self._should_terminate:
                return
            time.sleep(self.MIN_PUBLISH_INTERVAL_SECONDS)

    def _publish_metrics(self):
        try:
            items = self._get_items_from_queue()
            if items:
                metric_data = [item.to_record() for item in items]
                result = self._sagemaker_boto_client.batch_put_metrics(
                    ResourceArn=self._resource_arn,
                    MetricData=metric_data
                )
                if result['Errors']:
                    errors = []
                    for error in result['Errors']:
                        error = api_types.BatchPutMetricsError.from_boto(error)
                        error.metric_value = metric_data[error.metric_index]
                        errors.append(error)
                    self._last_exception = SageMakerMetricsWriterException('Errors on batch put metrics', errors)
        except Exception as ex:
            self._last_exception = ex

    def _get_items_from_queue(self):
        items = [self._work_queue.get()]
        for i in range(self.BATCH_MAX_SIZE - 1):
            try:
                items.append(self._work_queue.get_nowait())
            except queue.Empty:
                break
        self._should_terminate = self._terminate_message in items
        if self._should_terminate:
            items.remove(self._terminate_message)
        return items

    @property
    def has_error(self):
        return self._last_exception is not None

    @property
    def last_error(self):
        return self._last_exception

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        try:
            self._work_queue.put(
                _RawMetricData(metric_name=metric_name, value=value, timestamp=timestamp,
                               iteration_number=iteration_number)
            )
        except AttributeError:
            if self._closed:
                raise SageMakerMetricsWriterException('log_metric called on a closed writer')
            else:
                raise

    def close(self):
        if not self._closed:
            self._work_queue.put(self._terminate_message)
            self._publisher_thread.join(timeout=500)
            self._closed = True
            self._work_queue = None
            if self.raise_on_close and self.has_error:
                raise self.last_error

    def __enter__(self):
        """Return self"""
        return self

    def __exit__(self, type, value, traceback):
        """Execute self.close()"""
        self.close()

    def __del__(self):
        """Execute self.close()"""
        self.close()


class _RawMetricData(object):
    MetricName = None
    Value = None
    Timestamp = None
    IterationNumber = None

    def __init__(self, metric_name, value, timestamp=None, iteration_number=None, record_type='API'):
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()
        elif isinstance(timestamp, datetime.datetime):
            # If the input is a datetime then convert it to UTC time. Assume a naive datetime is in local timezone
            if not timestamp.tzinfo:
                timestamp = timestamp.replace(tzinfo=dateutil.tz.tzlocal())
            timestamp = (timestamp - timestamp.utcoffset()).replace(tzinfo=datetime.timezone.utc)
        else:
            timestamp = float(timestamp)
            timestamp = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=datetime.timezone.utc)
        if record_type == 'File':
            self.Timestamp = timestamp.timestamp()
        elif record_type == 'API':
            self.Timestamp = timestamp
        else:
            raise ValueError('Unknown record type %s' % record_type)

        value = float(value)
        self.MetricName = metric_name
        self.Value = float(value)

        if iteration_number is not None:
            assert isinstance(iteration_number, int)
            self.IterationNumber = iteration_number

    def to_record(self):
        return self.__dict__

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            ','.join(['{}={}'.format(k, repr(v)) for k, v in vars(self).items()]),
        )
