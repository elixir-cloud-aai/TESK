### Produce wheels and install them
############################################################

FROM alpine:3.7 as builder

RUN apk add --no-cache python2 py2-pip git
RUN pip install -U pip wheel

WORKDIR /app/
COPY tesk-core tesk-core
COPY .git .git

WORKDIR /app/tesk-core
RUN python setup.py bdist_wheel --dist-dir=/wheels/
RUN pip wheel --wheel-dir=/wheels /wheels/*.whl

RUN pip install /wheels/*.whl

RUN pip uninstall wheel -y
RUN apk del --no-cache py2-pip

### Copy and paste necessary bits to image
############################################################

FROM alpine:3.7

RUN apk add --no-cache curl openssl

# https://pkgs.alpinelinux.org/contents?branch=v3.7&name=python2&arch=x86_64&repo=main
COPY --from=builder /usr/bin/python /usr/bin/
COPY --from=builder /usr/bin/python2 /usr/bin/
COPY --from=builder /usr/bin/python2.7 /usr/bin/
COPY --from=builder /usr/lib/libpython2.7.so.1.0 /usr/lib/
COPY --from=builder /usr/lib/python2.7/ /usr/lib/python2.7/

COPY --from=builder /usr/bin/taskmaster.py /usr/bin/
COPY --from=builder /usr/bin/filer.py /usr/bin/
COPY --from=builder /usr/bin/job.py /usr/bin/
COPY --from=builder /usr/bin/pvc.py /usr/bin/
COPY --from=builder /usr/bin/filer_class.py /usr/bin/

RUN adduser -S taskmaster
USER taskmaster

ENTRYPOINT ["taskmaster.py"]
