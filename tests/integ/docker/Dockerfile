# Copyright 019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

FROM ubuntu:16.04

ARG script
ARG library
ARG botomodel
ARG endpoint

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        curl \
        ca-certificates \
        awscli \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py


WORKDIR /root

COPY $library .

# use a custom model if provided
RUN if [ "$botomodel" -a  -f "$botomodel" ]; then \
    cp "$botomodel" . \
    aws configure add-model --service-name sagemaker --service-model file://sagemaker-experiments-2017-07-24.normal.json; \
fi

RUN python3 -m pip install $(basename $library)

COPY $script script.py

ENV SAGEMAKER_ENDPOINT=${endpoint}

ENTRYPOINT ["python3", "./script.py"]
