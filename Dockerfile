FROM alpine:3.8

RUN apk update && \
    apk add --no-cache musl-dev gcc g++ make cmake libusb-dev pkgconf git python3 py3-requests

WORKDIR /root/tmp

RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    mkdir rtl-sdr/build

WORKDIR /root/tmp/rtl-sdr/build

RUN git checkout ed0317e6a58c098874ac58b769cf2e609c18d9a5 && \
    cmake ../ -DDETACH_KERNEL_DRIVER=ON && \
    make && \
    make install

WORKDIR /root/tmp

RUN git clone https://github.com/merbanan/rtl_433.git && \
    mkdir rtl_433/build

WORKDIR /root/tmp/rtl_433/build

RUN git checkout 6edb5d2bac0f1b41ef39e437263a43accd9bc1c4 && \
    cmake ../ && \
    make && \
    make install

WORKDIR /opt/logreposit/lacrosse-tx-reader-service

ADD src/lacrosse-tx-reader-service.py /opt/logreposit/lacrosse-tx-reader-service/lacrosse-tx-reader-service.py
ADD run.sh                            /opt/logreposit/lacrosse-tx-reader-service/run.sh

RUN chmod +x /opt/logreposit/lacrosse-tx-reader-service/lacrosse-tx-reader-service.py && \
    chmod +x /opt/logreposit/lacrosse-tx-reader-service/run.sh

CMD [ "sh", "-c", "/opt/logreposit/lacrosse-tx-reader-service/run.sh" ]
