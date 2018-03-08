FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip curl openssl
RUN pip install kubernetes

RUN adduser -S taskmaster

USER taskmaster

WORKDIR /home/taskmaster
COPY tesk_core/taskmaster.py .
COPY tesk_core/job.py .
COPY tesk_core/pvc.py .
COPY tesk_core/filer_class.py .

ENTRYPOINT ["/home/taskmaster/taskmaster.py"]
