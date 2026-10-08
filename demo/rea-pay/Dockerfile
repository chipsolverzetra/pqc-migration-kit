# Rea Pay demo image.
# DEMO FILE. Pins OpenSSL 1.1 for "legacy RSA tooling compatibility",
# which blocks any PQC-capable provider (those target OpenSSL 3.x).
FROM python:3.11-slim

# Legacy OpenSSL pinned on purpose for the demo. Do not do this.
RUN apt-get update && apt-get install -y openssl1.1 libssl1.1 \
    && rm -rf /var/lib/apt/lists

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Key material copied into the image for the demo. Do not do this.
COPY keys/ /app/keys/
COPY *.py /app/
COPY config.yaml /app/

CMD ["python", "ledger_service.py"]
