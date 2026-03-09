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
    socat \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy opencv-python-headless

RUN pip install --no-cache-dir --no-binary Pillow Pillow

RUN groupadd -r ctf && useradd -r -m -g ctf ctf

WORKDIR /home/ctf

COPY --chown=ctf:ctf server.py /home/ctf/
COPY --chown=ctf:ctf gen.py /home/ctf/
COPY --chown=ctf:ctf AppleColorEmoji-160px.ttf /home/ctf/
COPY --chown=ctf:ctf emojis_pool.json /home/ctf/

USER ctf

ENTRYPOINT ["socat", "-t", "850", "-T", "30", "TCP-LISTEN:1717,reuseaddr,nodelay,fork", "EXEC:python3 server.py"]

EXPOSE 1717/tcp
