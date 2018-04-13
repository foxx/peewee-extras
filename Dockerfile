FROM ubuntu:17.10

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    SHELL=/bin/bash

# Install apt-fast
RUN apt-get update && \
    apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository ppa:apt-fast/stable && \
    apt-get update && \
    apt-get -y install apt-fast

# install python deps
RUN apt-fast install -y -f python python-dev python-pip

# install python3 deps
RUN apt-fast install -y -f python3 python3-dev python3-pip python3-venv
RUN pip3 install --upgrade pip setuptools pipenv

# install lib deps
RUN apt-fast install -y -f libmysqlclient-dev libyaml-dev

# Install app deps
RUN mkdir -p /app
WORKDIR /app
ADD Pipfile /app/
RUN pipenv install --dev --skip-lock

VOLUME ["/app"]
