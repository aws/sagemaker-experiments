import enum
import json
import os
import time

from smexperiments import trial_component

TRAINING_JOB_ARN_ENV = "TRAINING_JOB_ARN"
PROCESSING_JOB_CONFIG_PATH = "/opt/ml/config/processingjobconfig.json"


class EnvironmentType(enum.Enum):
    SageMakerTrainingJob = 1
    SageMakerProcessingJob = 2


class TrialComponentEnvironment(object):

    environment_type = None
    source_arn = None

    def __init__(self, environment_type, source_arn):
        self.environment_type = environment_type
        self.source_arn = source_arn

    @classmethod
    def load(cls, training_job_arn_env=TRAINING_JOB_ARN_ENV, processing_job_config_path=PROCESSING_JOB_CONFIG_PATH):
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
