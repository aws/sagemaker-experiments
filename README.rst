=====================
SageMaker Experiments
=====================
Experiment tracking in SageMaker Training Jobs, Processing Jobs, and Notebooks.

Overview
--------
SageMaker Experiments is an AWS service for tracking machine learning Experiments. The SageMaker Experiments Python SDK is a high-level interface to this service that helps you track Experiment information using Python.

Concepts
--------

- Experiment: A collection of related Trials. Add Trials to an Experiment that you wish to compare together.
- Trial: A description of a multi-step machine learning workflow. Each step in the workflow is described by a TrialComponent.
- TrialComponent: A description of a single step in a machine learning workflow. 
- Tracker: A Python context-manager for logging information about a single TrialComponent.

Using the SDK
-------------
You can use this SDK to:

- Manage Experiments, Trials, and Trial Components within Python scripts, programs, and notebooks.
- Add tracking information to a SageMaker notebook, allowing you to model your notebook in SageMaker Experiments as a multi-step ML workflow.
- Record experiment information from inside your running SageMaker Training and Processing Jobs.

Examples
--------
See: `sagemaker-experiments <https://github.com/awslabs/amazon-sagemaker-examples/tree/master/sagemaker-experiments>`_ in `AWS Labs Amazon SageMaker Examples <https://github.com/awslabs/amazon-sagemaker-examples>`_. 

Installation
------------

``pip install sagemaker-experiments``.

License
-------
This library is licensed under the Apache 2.0 License. 
