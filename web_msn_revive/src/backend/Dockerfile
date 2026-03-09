FROM python:3.14-slim

RUN addgroup --system app && adduser --system --group app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
    "--workers", "4", \
    "-k", "gthread", \
    "--keep-alive", "30", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--preload", \
    "app:create_app()" \
]