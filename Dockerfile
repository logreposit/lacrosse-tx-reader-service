FROM alpine:3.8

RUN apk update && apk add --no-cache musl-dev gcc g++ make cmake libusb-dev pkgconf git python3 py3-requests

WORKDIR /root/tmp

RUN git clone git://git.osmocom.org/rtl-sdr.git
RUN mkdir rtl-sdr/build

WORKDIR /root/tmp/rtl-sdr/build

RUN cmake ../ -DDETACH_KERNEL_DRIVER=ON && make && make install

WORKDIR /root/tmp

RUN git clone https://github.com/merbanan/rtl_433.git
RUN mkdir rtl_433/build

WORKDIR /root/tmp/rtl_433/build

RUN cmake ../ && make && make install

WORKDIR /opt/logreposit/lacrosse-tx-reader-service

ADD src/lacrosse-tx-reader-service.py /opt/logreposit/lacrosse-tx-reader-service/lacrosse-tx-reader-service.py
ADD run.sh                            /opt/logreposit/lacrosse-tx-reader-service/run.sh

RUN chmod +x /opt/logreposit/lacrosse-tx-reader-service/lacrosse-tx-reader-service.py && \
    chmod +x /opt/logreposit/lacrosse-tx-reader-service/run.sh

CMD [ "sh", "-c", "/opt/logreposit/lacrosse-tx-reader-service/run.sh" ]
