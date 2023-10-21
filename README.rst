.. image:: https://github.com/aws/sagemaker-experiments/raw/main/branding/icon/sagemaker-banner.png
    :height: 100px
    :alt: SageMaker
    :target: https://aws.amazon.com/sagemaker/

**NOTE:** Use the SageMaker `SDK <https://sagemaker.readthedocs.io/en/v2.125.0/experiments/sagemaker.experiments.html>`_ to use SageMaker Experiments. This repository will not be up to date with the latest product improvements. Link to `developer guide <https://docs.aws.amazon.com/sagemaker/latest/dg/experiments.html>`_. 

================================
SageMaker Experiments Python SDK
================================

.. image:: https://img.shields.io/pypi/v/sagemaker-experiments.svg
    :target: https://pypi.python.org/pypi/sagemaker-experiments
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/sagemaker-experiments.svg
    :target: https://pypi.python.org/pypi/sagemaker-experiments
    :alt: Supported Python Versions

.. image:: https://img.shields.io/pypi/l/sagemaker-experiments
    :target: https://github.com/aws/sagemaker-experiments/blob/main/LICENSE
    :alt: License

.. image:: https://img.shields.io/pypi/dm/sagemaker-experiments
    :target: https://pypi.python.org/pypi/sagemaker-experiments
    :alt: PyPI - Downloads

.. image:: https://codecov.io/gh/aws/sagemaker-experiments/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/aws/sagemaker-experiments
   :alt: CodeCov

.. image:: https://img.shields.io/pypi/status/sagemaker-experiments
    :target: https://github.com/aws/sagemaker-experiments
    :alt: PyPI - Status

.. image:: https://img.shields.io/pypi/format/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: Kit format

.. image:: https://img.shields.io/github/actions/workflow/status/aws/sagemaker-experiments/test_release.yml?branch=main
    :target: https://github.com/aws/sagemaker-experiments/actions
    :alt: GitHub Workflow Status

.. image:: https://img.shields.io/github/stars/aws/sagemaker-experiments.svg?logo=github
    :target: https://github.com/aws/sagemaker-experiments/stargazers
    :alt: Github stars

.. image:: https://img.shields.io/github/forks/aws/sagemaker-experiments.svg?logo=github
    :target: https://github.com/aws/sagemaker-experiments/network/members
    :alt: Github forks

.. image:: https://img.shields.io/github/contributors/aws/sagemaker-experiments.svg?logo=github
    :target: https://github.com/aws/sagemaker-experiments/graphs/contributors
    :alt: Contributors

.. image:: https://img.shields.io/github/search/aws/sagemaker-experiments/sagemaker
    :target: https://github.com/aws/sagemaker-experiments
    :alt: GitHub search hit counter

.. image:: https://img.shields.io/badge/code_style-black-000000.svg
    :target: https://github.com/python/black
    :alt: Code style: black

.. image:: https://readthedocs.org/projects/sagemaker-experiments/badge/?version=latest
    :target: https://readthedocs.org/projects/sagemaker-experiments/
    :alt: Read the Docs - Sagemaker Experiments

.. image:: https://mybinder.org/badge_logo.svg
    :target: https://mybinder.org/v2/gh/aws/amazon-sagemaker-examples/main?filepath=sagemaker-experiments%2Fmnist-handwritten-digits-classification-experiment.ipynb



Experiment tracking in SageMaker Training Jobs, Processing Jobs, and Notebooks.

Overview
--------
SageMaker Experiments is an AWS service for tracking machine learning Experiments. The SageMaker Experiments Python SDK is a high-level interface to this service that helps you track Experiment information using Python.

Experiment tracking powers the machine learning integrated development environment `Amazon SageMaker Studio <https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio.html>`_.

For detailed API reference please go to: `Read the Docs <https://sagemaker-experiments.readthedocs.io>`_

Concepts
--------

- **Experiment**: A collection of related Trials. Add Trials to an Experiment that you wish to compare together.
- **Trial**: A description of a multi-step machine learning workflow. Each step in the workflow is described by a Trial Component. There is no relationship between Trial Components such as ordering.
- **Trial Component**: A description of a single step in a machine learning workflow.  For example data cleaning, feature extraction, model training, model evaluation, etc...
- **Tracker**: A Python context-manager for logging information about a single TrialComponent.

For more information see `Amazon SageMaker Experiments - Organize, Track, and Compare Your Machine Learning Trainings <https://aws.amazon.com/blogs/aws/amazon-sagemaker-experiments-organize-track-and-compare-your-machine-learning-trainings/>`_

Using the SDK
-------------
You can use this SDK to:

- Manage Experiments, Trials, and Trial Components within Python scripts, programs, and notebooks.
- Add tracking information to a SageMaker notebook, allowing you to model your notebook in SageMaker Experiments as a multi-step ML workflow.
- Record experiment information from inside your running SageMaker Training and Processing Jobs.

Installation
------------

.. code-block:: bash

    pip install sagemaker-experiments

Examples
--------

.. code-block:: python

    import boto3
    import pickle, gzip, numpy, json, os
    import io
    import numpy as np
    import sagemaker.amazon.common as smac
    import sagemaker
    from sagemaker import get_execution_role
    from sagemaker import analytics
    from smexperiments import experiment

    # Specify training container
    from sagemaker.amazon.amazon_estimator import get_image_uri
    container = get_image_uri(boto3.Session().region_name, 'linear-learner')

    # Load the dataset
    s3 = boto3.client("s3")
    s3.download_file("sagemaker-sample-files", "datasets/image/MNIST/mnist.pkl.gz", "mnist.pkl.gz")
    with gzip.open('mnist.pkl.gz', 'rb') as f:
        train_set, valid_set, test_set = pickle.load(f, encoding='latin1')

    vectors = np.array([t.tolist() for t in train_set[0]]).astype('float32')
    labels = np.where(np.array([t.tolist() for t in train_set[1]]) == 0, 1, 0).astype('float32')

    buf = io.BytesIO()
    smac.write_numpy_to_dense_tensor(buf, vectors, labels)
    buf.seek(0)

    key = 'recordio-pb-data'
    bucket = sagemaker.session.Session().default_bucket()
    prefix = 'sagemaker/DEMO-linear-mnist'
    boto3.resource('s3').Bucket(bucket).Object(os.path.join(prefix, 'train', key)).upload_fileobj(buf)
    s3_train_data = 's3://{}/{}/train/{}'.format(bucket, prefix, key)
    output_location = 's3://{}/{}/output'.format(bucket, prefix)

    my_experiment = experiment.Experiment.create(experiment_name='MNIST')
    my_trial = my_experiment.create_trial(trial_name='linear-learner')

    role = get_execution_role()
    sess = sagemaker.Session()

    linear = sagemaker.estimator.Estimator(container,
                                        role, 
                                        train_instance_count=1, 
                                        train_instance_type='ml.c4.xlarge',
                                        output_path=output_location,
                                        sagemaker_session=sess)
    linear.set_hyperparameters(feature_dim=784,
                            predictor_type='binary_classifier',
                            mini_batch_size=200)

    linear.fit(inputs={'train': s3_train_data}, experiment_config={
                "ExperimentName": my_experiment.experiment_name,
                "TrialName": my_trial.trial_name,
                "TrialComponentDisplayName": "MNIST-linear-learner",
            },)
    
    trial_component_analytics = analytics.ExperimentAnalytics(experiment_name=my_experiment.experiment_name)

    analytic_table = trial_component_analytics.dataframe()
    analytic_table

For more examples, check out: `sagemaker-experiments <https://github.com/aws/amazon-sagemaker-examples/tree/master/sagemaker-experiments>`_ in `AWS Labs Amazon SageMaker Examples <https://github.com/aws/amazon-sagemaker-examples>`_.

License
-------
This library is licensed under the Apache 2.0 License.

Running Tests
-------------

**Unit Tests**

.. code-block:: bash

    tox tests/unit

**Integration Tests**

To run the integration tests, the following prerequisites must be met:

- AWS account credentials are available in the environment for the boto3 client to use.
- The AWS account has an IAM role with SageMaker permissions.

.. code-block:: bash

    tox tests/integ

- Test against different regions

.. code-block:: bash

    tox -e py39 -- --region cn-north-1
    
**Docker Based Integration Tests**

Several integration tests rely on docker to push an image to ECR which is then used for training.

Docker Setup

1. Install docker
2. set aws cred helper in docker config (~/.docker/config.json)

.. code-block:: javascript

    # docker config example
    {
        "stackOrchestrator": "swarm",
        "credsStore": "desktop",
        "auths": {
            "https://index.docker.io/v1/": {}
        },
        "credHelpers": {
            "aws_account_id.dkr.ecr.region.amazonaws.com": "ecr-login"
        },
        "experimental": "disabled"
    }


.. code-block:: bash

    # run only docker based tests
    tox -e py39 -- tests/integ -m 'docker'
    
    # exclude docker based tests
    tox -e py39 -- tests/integ -m 'not docker'



Generate Docs
-------------

.. code-block:: bash

    tox -e docs
