FROM python:3.13.1


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY Pipfile Pipfile.lock /Lightweight_Django/


RUN pip install pipenv && pipenv install --system


COPY . /Lightweight_Django/
