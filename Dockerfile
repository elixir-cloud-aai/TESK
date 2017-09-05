FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip nginx
RUN pip install --no-cache-dir Flask gunicorn pika

COPY ./conf/tesk.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-enabled/tesk.conf /etc/nginx/sites-available/tesk.conf
RUN rc-service nginx start

COPY ./api/tesk.py /root/tesk.py
WORKDIR /root

CMD gunicorn tesk:app
