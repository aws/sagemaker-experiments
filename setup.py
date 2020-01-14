# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import glob
import os
from setuptools import setup, find_packages


def read(fname):
    """
    Args:
        fname:
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def read_version():
    return read("VERSION").strip()


# Declare minimal set for installation
required_packages = [
    "boto3>=1.10.32"
]

# Open readme with original (i.e. LF) newlines
# to prevent the all too common "`long_description_content_type` missing"
# bug (https://github.com/pypa/twine/issues/454)
with open('README.rst', 'r', newline='', encoding='utf-8') as readme_file:
    long_description = readme_file.read()
    long_description_content_type = 'text/x-rst'

setup(
    name="sagemaker-experiments",
    version=read_version(),
    description="Open source library for Experiment Tracking in SageMaker Jobs and Notebooks",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[os.path.splitext(os.path.basename(path))[0] for path in glob.glob("src/*.py")],
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    author="Amazon Web Services",
    url="https://github.com/aws/sagemaker-experiment-tracking/",
    license="Apache License 2.0",
    keywords="ML Amazon AWS AI Tensorflow MXNet",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
    install_requires=required_packages,
    extras_require={
        "test": [
            "tox==3.13.1",
            "flake8",
            "pytest==4.4.1",
            "pytest-cov",
            "pytest-coverage",
            "pytest-rerunfailures",
            "pytest-xdist"
        ]
    }
)
