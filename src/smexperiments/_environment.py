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
import enum
import json
import os
import time

from smexperiments import trial_component

TRAINING_JOB_ARN_ENV = "TRAINING_JOB_ARN"
PROCESSING_JOB_CONFIG_PATH = "/opt/ml/config/processingjobconfig.json"


class EnvironmentType(enum.Enum):
    """SageMaker jobs which data can be pulled from the environment."""

    SageMakerTrainingJob = 1
    SageMakerProcessingJob = 2


class TrialComponentEnvironment(object):
    """Retrieves job specific data from the environment.

    Attributes:
        environment_type (EnvironmentType): The environment type.
        source_arn (str): The ARN of the current job.
    """

    environment_type = None
    source_arn = None

    def __init__(self, environment_type, source_arn):
        self.environment_type = environment_type
        self.source_arn = source_arn

    @classmethod
    def load(cls, training_job_arn_env=TRAINING_JOB_ARN_ENV, processing_job_config_path=PROCESSING_JOB_CONFIG_PATH):
        """Loads source arn of current job from environment.

        Args:
            training_job_arn_env (str): The environment key for training job ARN.
            processing_job_config_path (str): The processing job config path.

        Returns:
            TrialComponentEnvironment: Job data loaded from the environment. None if config does not exist.
        """
        if training_job_arn_env in os.environ:
            environment_type = EnvironmentType.SageMakerTrainingJob
            source_arn = os.environ.get(training_job_arn_env)
            return TrialComponentEnvironment(environment_type, source_arn)
        elif os.path.exists(processing_job_config_path):
            environment_type = EnvironmentType.SageMakerProcessingJob
            source_arn = json.loads(open(processing_job_config_path).read())["ProcessingJobArn"]
            return TrialComponentEnvironment(environment_type, source_arn)
        else:
            return None

    def get_trial_component(self, sagemaker_boto_client):
        """Retrieves the trial component from the job in the environment.

        Args:
            sagemaker_boto_client (SageMaker.Client): SageMaker boto client.

        Returns:
            TrialComponent: The trial component created from the job. None if not found.
        """
        start = time.time()
        while time.time() - start < 300:
            summaries = list(
                trial_component.TrialComponent.list(
                    source_arn=self.source_arn, sagemaker_boto_client=sagemaker_boto_client
                )
            )
            if summaries:
                summary = summaries[0]
                return trial_component.TrialComponent.load(
                    trial_component_name=summary.trial_component_name, sagemaker_boto_client=sagemaker_boto_client
                )
            else:
                time.sleep(2)
        return None
