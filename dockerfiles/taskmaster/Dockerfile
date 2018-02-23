FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip curl openssl
RUN pip install kubernetes

RUN adduser -S taskmaster

USER taskmaster

WORKDIR /home/taskmaster
COPY scripts/taskmaster.py .
COPY scripts/job.py .
COPY scripts/pvc.py .
COPY scripts/filer_class.py .

ENTRYPOINT ["/home/taskmaster/taskmaster.py"]
