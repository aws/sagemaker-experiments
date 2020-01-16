.. image:: https://github.com/aws/sagemaker-experiments/raw/master/branding/icon/sagemaker-banner.png
    :height: 100px
    :alt: SageMaker
    :target: https://aws.amazon.com/sagemaker/

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
    :target: https://github.com/aws/sagemaker-experiments/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/dm/sagemaker-experiments
    :target: https://pypi.python.org/pypi/sagemaker-experiments
    :alt: PyPI - Downloads

Experiment tracking in SageMaker Training Jobs, Processing Jobs, and Notebooks.

Overview
--------
SageMaker Experiments is an AWS service for tracking machine learning Experiments. The SageMaker Experiments Python SDK is a high-level interface to this service that helps you track Experiment information using Python.

Experiment tracking powers the machine learning integrated development environment `Amazon SageMaker Studio <https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio.html>`_.

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
See: `sagemaker-experiments <https://github.com/awslabs/amazon-sagemaker-examples/tree/master/sagemaker-experiments>`_ in `AWS Labs Amazon SageMaker Examples <https://github.com/awslabs/amazon-sagemaker-examples>`_.

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