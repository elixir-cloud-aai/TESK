FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip curl openssl
RUN pip install kubernetes

WORKDIR /root
COPY scripts/taskmaster.py .

ENTRYPOINT ["/root/taskmaster.py"]
#CMD /root/taskmaster.py
