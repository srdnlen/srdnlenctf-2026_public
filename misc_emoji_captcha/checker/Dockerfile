FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    libfreetype6-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    libraqm-dev \
    libjpeg-dev \
    zlib1g-dev \
    ncurses-term

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy opencv-python-headless requests pwntools

RUN pip install --no-cache-dir --no-binary Pillow Pillow

WORKDIR /app