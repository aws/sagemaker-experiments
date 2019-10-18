# Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
"""Placeholder docstring"""
from __future__ import absolute_import

import os
import sys
import uuid
import boto3


class Tracker(object):
    """
    Create a tracker to log metrics and artifacts.
    """

    def __init__(self, name=None, display_name=None, source_arn=None, sagemaker_boto_client=None):
        self.sagemaker_boto_client = sagemaker_boto_client or self._default_sagemaker_boto_client()
        self.source_arn = source_arn or self._resolve_source_arn()
        self.failed_mode = False
        self.component_name = None

        if self.source_arn and self._has_auto_created_trial_component(self.source_arn):
            try:
                self.component_name = self._get_component_name(self.source_arn)
            except:
                # We do not want training job to fail if we cant find the auto-created component
                e = sys.exc_info()
                print("Unable to get the trial component name for "
                      "source arn : {} due to : {}".format(self.source_arn, str(e)))
                self.failed_mode = True
        else:
            if not display_name:
                raise ValueError("Please specify a valid display_name.")
            self.component_name = name if name else self._generate_component_name(display_name)
            self._create_trial_component(self.component_name, display_name, self.source_arn)

    def _create_trial_component(self, component_name, display_name, source_arn):
        """Placeholder docstring"""
        self.sagemaker_boto_client.create_trial_component(
            TrialComponentName=component_name,
            DisplayName=display_name,
            Source={"SourceArn": source_arn},
        )

    @staticmethod
    def _generate_component_name(display_name):
        """Placeholder docstring"""
        return "{}-{}".format(display_name, str(uuid.uuid4()))

    @staticmethod
    def _resolve_source_arn():
        """
        Resolves the source arn from the environment
        """
        source_arn_env_keys = ["TRAINING_JOB_ARN"]
        return next(
            (
                os.environ.get(source_arn_env_key)
                for source_arn_env_key in source_arn_env_keys
                if os.environ.get(source_arn_env_key)
            ),
            None,
        )

    def _get_component_name(self, source_arn):
        response = self.sagemaker_boto_client.list_trial_components(
            SourceArn=source_arn
        )
        component_summaries = response.get("TrialComponents")
        # There should only be one trial component for a given source arn
        summary = component_summaries[0]
        return summary.get("TrialComponentName")

    @staticmethod
    def _default_sagemaker_boto_client():
        """Placeholder docstring"""
        return boto3.client("sagemaker")

    @staticmethod
    def _has_auto_created_trial_component(source_arn):
        """Placeholder docstring"""
        auto_created_types = ["training-job", "tuning-job", "transform-job", "analytics-job"]
        for entity_type in auto_created_types:
            if "{}/".format(entity_type) in source_arn:
                return True
        return False
