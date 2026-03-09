FROM python:3.11-slim

# Prevent buffering (important for MJPEG streaming)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir flask pillow

COPY camera.py /app/camera.py

EXPOSE 80

CMD ["python", "camera.py"]

