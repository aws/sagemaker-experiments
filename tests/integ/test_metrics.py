import statistics
import unittest

from smexperiments import metrics
from tests.fixtures import *
from tests.helpers import *


def test_api_writer(trial_component_obj, sagemaker_boto_client):
    metric_name = name()
    resource_arn = trial_component_obj.trial_component_arn
    N = metrics.SageMakerMetricsWriter.QUEUE_SIZE + 1
    with metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client, raise_on_close=True) as w:
        for i in range(N):
            w.log_metric(metric_name, i)
    expect_stat(sagemaker_boto_client, resource_arn, metric_name, 'Max', N - 1)
    expect_stat(sagemaker_boto_client, resource_arn, metric_name, 'Min', 0)
    expect_stat(sagemaker_boto_client, resource_arn, metric_name, 'Count', N)
    expect_stat(sagemaker_boto_client, resource_arn, metric_name, 'StdDev', statistics.stdev(range(N)))
    expect_stat(sagemaker_boto_client, resource_arn, metric_name, 'Avg', statistics.mean(range(N)))


def test_api_writer_fail(sagemaker_boto_client):
    metric_name = name()
    N = 1
    with pytest.raises(Exception):
        with metrics.SageMakerMetricsWriter('not an arn', sagemaker_boto_client, raise_on_close=True) as w:
            for i in range(N):
                w.log_metric(metric_name, i, timestamp=i)


def test_api_writer_metric_summaries(trial_component_obj, sagemaker_boto_client):
    metric_name = name()
    resource_arn = trial_component_obj.trial_component_arn
    N = metrics.SageMakerMetricsWriter.QUEUE_SIZE + 1
    with metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client, raise_on_close=True) as w:
        for i in range(N):
            w.log_metric(metric_name=metric_name, value=i)

    def validate(trial_component_name):
        trial_component_obj = trial_component.TrialComponent.load(
            trial_component_name=trial_component_name, sagemaker_boto_client=sagemaker_boto_client)
        [metric_summary] = trial_component_obj.metrics
        assert metric_summary.metric_name == metric_name
        assert metric_summary.count == N
        assert metric_summary.min == 0
        assert metric_summary.max == N - 1
        unittest.TestCase().assertAlmostEqual(metric_summary.avg, statistics.mean(range(N)), places=4)
        unittest.TestCase().assertAlmostEqual(metric_summary.std_dev, statistics.stdev(range(N)), places=4)

    retry(lambda : validate(trial_component_name=trial_component_obj.trial_component_name), num_attempts=8)


def test_api_writer_iteration_number(trial_component_obj, sagemaker_boto_client):
    metric_name = name()
    resource_arn = trial_component_obj.trial_component_arn
    N = metrics.SageMakerMetricsWriter.QUEUE_SIZE + 1
    with metrics.SageMakerMetricsWriter(resource_arn, sagemaker_boto_client, raise_on_close=True) as w:
        for i in range(N):
            w.log_metric(metric_name=metric_name, value=i, iteration_number=i)
