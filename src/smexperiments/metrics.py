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
"""Metrics module"""
import datetime
import json
import logging
import os
import time

import dateutil.tz


METRICS_DIR = os.environ.get("SAGEMAKER_METRICS_DIRECTORY", ".")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SageMakerFileMetricsWriter(object):
    """Writes metric data to file."""

    def __init__(self, metrics_file_path=None):
        self._metrics_file_path = metrics_file_path
        self._file = None
        self._closed = False

    def log_metric(self, metric_name, value, timestamp=None, iteration_number=None):
        """Write a metric to file.

        Args:
            metric_name (str): The name of the metric.
            value (str): The value of the metric.
            timestamp (datetime): Timestamp of the metric.
            iteration_number (int):  Iteration number of the metric.

        Raises:
            SageMakerMetricsWriterException: If the metrics file is closed.
            AttributeError: If file has been initialized and the writer hasn't been closed.
        """
        raw_metric_data = _RawMetricData(
            metric_name=metric_name, value=value, timestamp=timestamp, iteration_number=iteration_number
        )
        try:
            logging.debug("Writing metric: %s", raw_metric_data)
            self._file.write(json.dumps(raw_metric_data.to_record()))
            self._file.write("\n")
        except AttributeError:
            if self._closed:
                raise SageMakerMetricsWriterException("log_metric called on a closed writer")
            elif not self._file:
                self._file = open(self._get_metrics_file_path(), "a", buffering=1)
                self._file.write(json.dumps(raw_metric_data.to_record()))
                self._file.write("\n")
            else:
                raise

    def close(self):
        """Closes the metric file."""
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
        pid_filename = "{}.json".format(str(os.getpid()))
        metrics_file_path = self._metrics_file_path or os.path.join(METRICS_DIR, pid_filename)
        logging.debug("metrics_file_path=" + metrics_file_path)
        return metrics_file_path


class SageMakerMetricsWriterException(Exception):
    """SageMakerMetricsWriterException"""

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

        if timestamp < (time.time() - 1209600) or timestamp > (time.time() + 7200):
            raise ValueError(
                "Supplied timestamp %f is invalid."
                " Timestamps must be between two weeks before and two hours from now." % timestamp
            )
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
        return "{}({})".format(
            type(self).__name__,
            ",".join(["{}={}".format(k, repr(v)) for k, v in vars(self).items()]),
        )
