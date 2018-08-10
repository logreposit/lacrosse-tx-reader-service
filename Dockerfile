FROM alpine:3.8

WORKDIR /root/tmp

RUN apk update && apk add --no-cache musl-dev gcc make cmake libusb-dev pkgconf git python3
RUN git clone git://git.osmocom.org/rtl-sdr.git
RUN mkdir rtl-sdr/build

WORKDIR /root/tmp/rtl-sdr/build

RUN cmake ../ -DDETACH_KERNEL_DRIVER=ON && make && make install

WORKDIR /opt/logreposit/lacrosse-tx-reader-service

ADD src/lacrosse_reader_service.py /opt/logreposit/lacrosse-tx-reader-service/lacrosse_reader_service.py
ADD run.sh                         /opt/logreposit/lacrosse-tx-reader-service/run.sh

RUN chmod +x /opt/logreposit/lacrosse-tx-reader-service/run.sh

ENTRYPOINT [ "/opt/logreposit/lacrosse-tx-reader-service/run.sh" ]
