FROM ubuntu:16.04

ARG script
ARG library
ARG botomodel

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

COPY $botomodel .

RUN aws configure add-model --service-model file://$(basename $botomodel) --service-name sagemaker

RUN python3 -m pip install $(basename $library)

COPY $script script.py

ENTRYPOINT ["python3", "./script.py"]
