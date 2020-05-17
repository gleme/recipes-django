FROM python:3.8-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/recipes-django

RUN apk add --update --no-cache postgresql-client jpeg-dev

RUN apk add --update --no-cache --virtual .tmp-build-deps \
        gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

RUN apk del .tmp-build-deps

COPY ./src .
COPY .flake8 .

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

RUN adduser -D python

RUN chown -R python:python /vol/
RUN chmod -R 755 /vol/web

USER python
