FROM python:3.7-alpine

RUN pip install --upgrade pip
RUN pip install requests==2.22.0

WORKDIR /app
COPY . .

CMD ["python3", "/app/review_app_status.py"]
