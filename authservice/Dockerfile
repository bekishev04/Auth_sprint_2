FROM python:3.10.2 as build

RUN apt-get update \
    && apt-get -y --no-install-recommends install supervisor locales \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

FROM build

WORKDIR /home/authservice
COPY pyproject.toml .

RUN ~/.local/bin/poetry export --without-hashes -f requirements.txt --output requirement.txt

RUN pip install -U pip
RUN pip install -r requirement.txt --no-cache-dir

COPY . .

ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU.UTF-8

CMD gunicorn manage:app -b 0.0.0.0:8000 --reload
