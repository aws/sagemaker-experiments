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

COPY $botomodel .

COPY $library .

RUN aws configure add-model --service-name sagemaker --service-model file://sagemaker-experiments-2017-07-24.normal.json 

RUN python3 -m pip install $(basename $library)

COPY $script script.py

ENV SAGEMAKER_ENDPOINT=${endpoint}

ENTRYPOINT ["python3", "./script.py"]
