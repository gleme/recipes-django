FROM python:3.8-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/recipes-django

RUN apk add --update --no-cache postgresql-client

RUN apk add --update --no-cache --virtual .tmp-build-deps \
        gcc libc-dev linux-headers postgresql-dev

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

RUN apk del .tmp-build-deps

COPY ./src ./

RUN adduser -D python

USER python