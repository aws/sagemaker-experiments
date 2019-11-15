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
import time

import dateutil.tz


METRICS_DIR = os.environ.get('SAGEMAKER_METRICS_DIRECTORY', '.')


class SageMakerFileMetricsWriter(object):

    def __init__(self, metrics_file_path=None):
        self._metrics_file_path = metrics_file_path
        self._file = None
        self._closed = False

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        raw_metric_data = _RawMetricData(metric_name=metric_name, value=value, timestamp=timestamp,
                                         iteration_number=iteration_number)
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


class SageMakerMetricsWriterException(Exception):

    def __init__(self, message, errors=None):
        super().__init__(message)
        if errors:
            self.errors = errors


class _RawMetricData(object):
    MetricName = None
    Value = None
    Timestamp = None
    IterationNumber = None

    def __init__(self, metric_name, value, timestamp=None, iteration_number=None):
        if timestamp is None:
            timestamp = time.time()
        elif isinstance(timestamp, datetime.datetime):
            # If the input is a datetime then convert it to UTC time. Assume a naive datetime is in local timezone
            if not timestamp.tzinfo:
                timestamp = timestamp.replace(tzinfo=dateutil.tz.tzlocal())
            timestamp = (timestamp - timestamp.utcoffset()).replace(tzinfo=datetime.timezone.utc)
            timestamp = timestamp.timestamp()
        else:
            timestamp = float(timestamp)

        value = float(value)

        self.MetricName = metric_name
        self.Value = float(value)
        self.Timestamp = timestamp
        if iteration_number is not None:
            assert isinstance(iteration_number, int)
            self.IterationNumber = iteration_number

    def to_record(self):
        return self.__dict__

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            ','.join(['{}={}'.format(k, repr(v)) for k, v in vars(self).items()]),
        )