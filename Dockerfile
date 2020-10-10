FROM debian:buster
#FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update && \
    apt-get -y install \
      cmake \
      build-essential \
      libusb-1.0-0-dev \
      pkg-config \
      git \
      python3 \
      python3-requests \
      python3-yaml

WORKDIR /root/tmp

RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    cd ./rtl-sdr && \
    git checkout ed0317e6a58c098874ac58b769cf2e609c18d9a5 && \
    mkdir ./build

WORKDIR /root/tmp/rtl-sdr/build

RUN cmake ../ -DDETACH_KERNEL_DRIVER=ON && \
    make && \
    make install && \
    ldconfig

WORKDIR /root/tmp

RUN git clone https://github.com/merbanan/rtl_433.git && \
    cd ./rtl_433 && \
    git checkout 6edb5d2bac0f1b41ef39e437263a43accd9bc1c4 && \
    mkdir ./build

WORKDIR /root/tmp/rtl_433/build

RUN cmake ../ && \
    make && \
    make install && \
    ldconfig

WORKDIR /opt/logreposit/lacrosse-tx-reader-service

ADD src/lacrosse-tx-reader-service.py /opt/logreposit/lacrosse-tx-reader-service/lacrosse-tx-reader-service.py
ADD src/device-definition.yaml        /opt/logreposit/lacrosse-tx-reader-service/device-definition.yaml
ADD run.sh                            /opt/logreposit/lacrosse-tx-reader-service/run.sh

RUN chmod +x /opt/logreposit/lacrosse-tx-reader-service/lacrosse-tx-reader-service.py && \
    chmod +x /opt/logreposit/lacrosse-tx-reader-service/run.sh

CMD [ "sh", "-c", "/opt/logreposit/lacrosse-tx-reader-service/run.sh" ]
