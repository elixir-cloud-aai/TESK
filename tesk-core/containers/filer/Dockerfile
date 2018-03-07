FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip
RUN pip install requests

WORKDIR /root
COPY ../../tesk_core/filer.py .

ENTRYPOINT ["/root/filer.py"]
