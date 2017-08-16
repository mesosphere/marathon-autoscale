FROM python:3-alpine
ADD / /marathon-autoscale
WORKDIR /marathon-autoscale
RUN apk add --update --virtual .build-dependencies openssl-dev libffi-dev python-dev make gcc g++
RUN pip install -r requirements.txt
CMD python marathon_autoscaler.py
