FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY synology_cert_updater.py .
RUN chmod +x synology_cert_updater.py

CMD ["python", "synology_cert_updater.py"]
