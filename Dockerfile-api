FROM gliderlabs/alpine

# install packages
RUN apk add --no-cache python py-pip nginx
RUN pip install --no-cache-dir Flask gunicorn pika

# create nginx folders
RUN mkdir /etc/nginx/sites-enabled
RUN mkdir /run/nginx

# copy main nginx conf
COPY ./conf/nginx.conf /etc/nginx/nginx.conf

# copy site conf and link
COPY ./conf/tesk.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/tesk.conf /etc/nginx/sites-enabled/

# rewire log output for docker container purposes
RUN ln -sf /dev/stderr /var/log/nginx/error.log
RUN ln -sf /dev/stdout /var/log/nginx/access.log

# copy python files
COPY ./api/tesk.py /root/tesk.py
WORKDIR /root

# expose web ports
EXPOSE 80 443

# start nginx & gunicorn
CMD /usr/sbin/nginx && gunicorn tesk:app
