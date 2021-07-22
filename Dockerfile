FROM python:3.9.6-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app/

RUN apt-get update && \
    apt-get install -y \
    bash \
    build-essential \
    gcc \
    libffi-dev \
    musl-dev \
    openssl \
    postgresql \
    libpq-dev

COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY *.py ./
COPY Procfile ./Procfile
COPY .env ./.env

ENTRYPOINT ["python", "bot.py"]