FROM python:3.7-alpine

RUN pip install --upgrade pip
RUN pip install requests==2.22.0

COPY review_app_status.py /

ENTRYPOINT ["python3", "/review_app_status.py"]
