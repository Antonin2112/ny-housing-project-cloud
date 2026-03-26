FROM grafana/k6:latest AS k6-bin
FROM python:3.11-alpine

# Copie le binaire k6 depuis l'image officielle
COPY --from=k6-bin /usr/bin/k6 /usr/bin/k6

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY server.py .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
