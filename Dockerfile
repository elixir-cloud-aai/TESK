FROM gliderlabs/alpine

RUN apk add --no-cache python py-pip nginx
RUN pip install --no-cache-dir Flask gunicorn pika

COPY ./conf/tesk.conf /etc/nginx/sites-available/
RUN mkdir /etc/nginx/sites-enabled
RUN ln -s /etc/nginx/sites-available/tesk.conf /etc/nginx/sites-enabled/
RUN /usr/sbin/nginx

COPY ./api/tesk.py /root/tesk.py
WORKDIR /root

CMD gunicorn tesk:app
