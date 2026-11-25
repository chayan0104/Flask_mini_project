FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py gunicorn.conf.py ./

EXPOSE 8080

ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-multiproc

CMD ["gunicorn", "--config", "gunicorn.conf.py", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
