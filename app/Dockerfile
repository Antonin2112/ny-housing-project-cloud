FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

#CMD [ "python3", "app.py" ]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "20","--backlog", "512", "--timeout", "30"]