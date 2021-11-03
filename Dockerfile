FROM python:3.6

RUN apt-get update && apt-get upgrade -y
RUN pip install --upgrade pip

COPY requirements /requirements
RUN pip install -r /requirements/torch.txt
RUN pip install -r /requirements/requirements.txt

COPY capts /capts