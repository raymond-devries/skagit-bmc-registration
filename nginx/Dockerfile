FROM nginx:mainline

COPY nginx.conf /home/
ADD start.sh /
RUN chmod +x /start.sh
RUN /start.sh

RUN apt-get -y update
RUN apt-get -y install software-properties-common

RUN apt-get -y install python-certbot-nginx