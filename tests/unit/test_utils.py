import os
import botocore
import pytest
import unittest
from unittest.mock import Mock, MagicMock

from smexperiments import _utils


@pytest.fixture
def boto3_session():
    mocked = Mock()
    mocked.client.return_value.get_caller_identity.return_value = {"Account": "testaccountid123"}
    mocked.region_name = "testregion"
    return mocked


def test_sagemaker_client_endpoint_env_set():
    current_endpoint = os.environ.get("SAGEMAKER_ENDPOINT")
    current_region = os.environ.get("AWS_REGION")

    os.environ["SAGEMAKER_ENDPOINT"] = "https://notexist.amazon.com"
    os.environ["AWS_REGION"] = "arc-north-1"

    client = _utils.sagemaker_client()

    assert client._endpoint.host == "https://notexist.amazon.com"

    os.environ["SAGEMAKER_ENDPOINT"] = current_endpoint if current_endpoint is not None else ""
    os.environ["AWS_REGION"] = current_region if current_region is not None else ""


def test_get_or_create_default_bucket_bucket_already_owned(boto3_session):
    exception = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "BucketAlreadyOwnedByYou", "Message": "BucketAlreadyOwnedByYou"}},
        operation_name="CreateBucket",
    )
    s3_mock = Mock()
    s3_mock.create_bucket.side_effect = exception
    boto3_session.resource.return_value = s3_mock

    bucket = _utils.get_or_create_default_bucket(boto3_session)

    assert bucket == "sagemaker-testregion-testaccountid123"


def test_get_or_create_default_bucket_operation_aborted(boto3_session):
    exception = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "OperationAborted", "Message": "foo conflicting conditional operation bar"}},
        operation_name="CreateBucket",
    )
    s3_mock = Mock()
    s3_mock.create_bucket.side_effect = exception
    boto3_session.resource.return_value = s3_mock

    bucket = _utils.get_or_create_default_bucket(boto3_session)

    assert bucket == "sagemaker-testregion-testaccountid123"


def test_get_or_create_default_bucket_too_many_buckets(boto3_session):
    exception = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "TooManyBuckets", "Message": "too many buckets"}},
        operation_name="CreateBucket",
    )
    s3_mock = MagicMock()
    s3_mock.create_bucket.side_effect = exception
    boto3_session.resource.return_value = s3_mock

    bucket = _utils.get_or_create_default_bucket(boto3_session)

    assert s3_mock.meta.client.head_bucket.called
    s3_mock.meta.client.head_bucket.assert_called_once_with(Bucket=bucket)
    assert bucket == "sagemaker-testregion-testaccountid123"


def test_get_or_create_default_other_error(boto3_session):
    exception = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "RequestTimeTooSkewed",
                "Message": "The difference between the request time and the server's time is too large.",
            }
        },
        operation_name="CreateBucket",
    )
    s3_mock = MagicMock()
    s3_mock.create_bucket.side_effect = exception
    boto3_session.resource.return_value = s3_mock

    with pytest.raises(botocore.exceptions.ClientError):
        bucket = _utils.get_or_create_default_bucket(boto3_session)
