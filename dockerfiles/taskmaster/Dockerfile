FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip curl openssl
RUN pip install kubernetes

WORKDIR /root
COPY taskmaster.py .

ENTRYPOINT /root/taskmaster.py
