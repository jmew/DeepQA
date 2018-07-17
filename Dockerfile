## Dockerfile to build DeepQ&A container image

FROM nvidia/cuda:9.0-cudnn5-devel

## Dependencies

RUN \
  apt-get -qq -y update && apt-get -y install unzip python3 python3-pip

RUN  \
  pip3 install -U nltk \
  tqdm \
  django \
  asgi_redis \
  channels && \
  python3 -m nltk.downloader punkt

## Tensorflow
ARG TF_BINARY_URL=https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-1.0.0-cp34-cp34m-linux_x86_64.whl
RUN \
  pip3 install -U $TF_BINARY_URL

COPY ./ /root/DeepQA

## Run Config

WORKDIR /root/DeepQA

