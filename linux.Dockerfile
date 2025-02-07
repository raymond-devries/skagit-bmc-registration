FROM public.ecr.aws/amazonlinux/amazonlinux:latest

WORKDIR /bmc-app
RUN yum install -y python3.11 python3.11-pip

COPY requirements.txt requirements.txt
RUN pip3.11 install -r requirements.txt
COPY registration registration
COPY SkagitRegistration SkagitRegistration
COPY static static
COPY templates templates
COPY manage.py manage.py

ENTRYPOINT [ "python3.11" ]