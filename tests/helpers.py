import time


def retry(callable, num_attempts = 3):
    assert num_attempts >= 1
    for i in range(num_attempts):
        try:
            return callable()
        except Exception as ex:
            if i == num_attempts - 1:
                raise ex
            print('Retrying', ex)
            time.sleep(2 ** i)
    assert False, 'logic error in retry'


def expect_stat(sagemaker_boto_client, resource_arn, metric_name, statistic, value,
                period='OneMinute', x_axis_type='Timestamp'):
    result = {}
    slack = 0.01
    for i in range(100):
        result = sagemaker_boto_client.batch_get_metrics(
            MetricQueries=[
                {
                    "MetricName": metric_name,
                    "ResourceArn": resource_arn,
                    "MetricStat": statistic,
                    "Period": period,
                    "XAxisType": x_axis_type
                }
            ]
        )['MetricQueryResults']
        result = result[0]
        if result['Status'] == 'Complete':
            [statistic_value] = result['MetricValues']
            assert statistic_value * (1.0 - slack) <= value <= statistic_value * (1.0 + slack), \
                'Actual: {}, Expected: {}'.format(str(result), value)
            return
    assert False, "Timed out waiting for statistic, last result {}".format(str(result))
