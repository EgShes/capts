FROM python:3.6

RUN apt-get update
RUN pip install --upgrade pip

COPY requirements.txt /requrements.txt
RUN pip install -r /requrements.txt

COPY capts /capts