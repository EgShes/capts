# syntax=docker/dockerfile:1.3
FROM ubuntu:20.04 as data

ARG WEIGHTS_GOOGLE_TOKEN

RUN apt update \
    && apt install wget -y

RUN wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=$WEIGHTS_GOOGLE_TOKEN" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=$WEIGHTS_GOOGLE_TOKEN" -O /tmp/weights.tar \
    && tar -xf /tmp/weights.tar

FROM python:3.6

COPY --from=data /weights /weights

RUN apt-get update && apt-get upgrade -y
RUN --mount=type=cache,target=/root/.cache \
    pip install --upgrade pip==21.3.1

COPY requirements /requirements
RUN --mount=type=cache,target=/root/.cache \
    pip install -r /requirements/torch.txt
RUN --mount=type=cache,target=/root/.cache \
    pip install -r /requirements/requirements.txt

COPY capts /capts
