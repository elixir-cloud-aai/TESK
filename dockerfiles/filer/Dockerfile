FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip
RUN pip install requests

WORKDIR /root
COPY scripts/filer.py .

ENTRYPOINT ["/root/filer.py"]
#CMD /root/taskmaster.py
