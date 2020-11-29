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
import os
import random
import time

import boto3
import botocore
import logging
from importlib import import_module


def sagemaker_client():
    """Instantiates a SageMaker client.

    Returns:
        SageMaker.Client
    """
    if os.environ.get("SAGEMAKER_ENDPOINT", "").strip():
        return boto_session().client("sagemaker", endpoint_url=os.environ.get("SAGEMAKER_ENDPOINT"))
    else:
        return boto_session().client("sagemaker")


def boto_session():
    """Instantiates a boto Session.

    Returns:
        boto3.Session
    """
    return boto3.Session(region_name=os.environ.get("AWS_REGION"))


def suffix():
    """Generate a random string of length 4"""
    alph = "abcdefghijklmnopqrstuvwxyz"
    return "-".join([time.strftime("%Y-%m-%d-%H%M%S"), "".join(random.sample(alph, 4))])


def name(prefix):
    """Generate a new name with the specified prefix."""
    return "-".join([prefix, suffix()])


def get_or_create_default_bucket(boto_session, default_bucket_prefix="sagemaker"):
    """Creates a default bucket if not already exists. The bucket name is a combination of a prefix, the region, and
    account.

    Args:
        boto_session (boto3.Session): boto session
        default_bucket_prefix (str): prefix to the bucket name

    Returns:
        str: The default bucket name.
    """
    account = boto_session.client("sts").get_caller_identity()["Account"]
    region = boto_session.region_name
    default_bucket = "{}-{}-{}".format(default_bucket_prefix, region, account)

    s3 = boto_session.resource("s3")
    try:
        # 'us-east-1' cannot be specified because it is the default region:
        if region == "us-east-1":
            s3.create_bucket(Bucket=default_bucket)
        else:
            s3.create_bucket(Bucket=default_bucket, CreateBucketConfiguration={"LocationConstraint": region})

    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        message = e.response["Error"]["Message"]
        logging.debug("Create Bucket failed. error code: {}, message: {}".format(error_code, message))

        if error_code == "BucketAlreadyOwnedByYou":
            pass
        elif error_code == "OperationAborted" and "conflicting conditional operation" in message:
            # If this bucket is already being concurrently created, we don't need to create it again.
            pass
        elif error_code == "TooManyBuckets":
            # Succeed if the default bucket exists
            s3.meta.client.head_bucket(Bucket=default_bucket)
        else:
            raise
    return default_bucket


def get_module(module_name):
    """Imports an module.

    Args:
        module_name (str): Name of the module to importt.

    Returns:
        [obj]: The imported module
    """
    return import_module(module_name)
