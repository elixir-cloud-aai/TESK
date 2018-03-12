### Produce wheels inside an image
############################################################

FROM python:2.7-alpine as builder

RUN apk add --no-cache git

WORKDIR /app/
COPY tesk-core tesk-core
COPY .git .git

WORKDIR /app/tesk-core
RUN python setup.py bdist_wheel --dist-dir=/wheels/
RUN pip wheel --wheel-dir=/wheels /wheels/*.whl

### Stage the wheels installation to image
############################################################

FROM alpine:3.7 as staging

COPY --from=builder /wheels /wheels

RUN apk add --no-cache python2 py-pip
RUN pip install /wheels/*.whl
RUN apk del --no-cache py-pip

### Deployable image
############################################################

FROM alpine:3.7

RUN apk add --no-cache curl openssl

# https://pkgs.alpinelinux.org/contents?branch=v3.7&name=python2&arch=x86_64&repo=main
COPY --from=staging /usr/bin/python /usr/bin/
COPY --from=staging /usr/bin/python2 /usr/bin/
COPY --from=staging /usr/bin/python2.7 /usr/bin/
COPY --from=staging /usr/lib/libpython2.7.so.1.0 /usr/lib/
COPY --from=staging /usr/lib/python2.7/ /usr/lib/python2.7/

COPY --from=staging /usr/bin/filer.py /usr/bin/

RUN adduser -S filer
USER filer

ENTRYPOINT ["filer.py"]
