FROM python:3-alpine
ADD / /marathon-autoscale
WORKDIR /marathon-autoscale
RUN pip install -r requirements.txt
CMD python marathon_autoscaler.py
