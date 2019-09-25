FROM python:3.7-alpine

LABEL version="1.0.1" \
  repository="https://github.com/niteoweb/reviewapps-deploy-status" \
  homepage="https://github.com/niteoweb" \
  maintainer="niteo.co" \
  "com.github.actions.name"="Heroku Review App Deployment Status" \
  "com.github.actions.description"="A Github Action to test the deployment status of a Heroku Review App." \
  "com.github.actions.icon"="git-pull-request" \
  "com.github.actions.color"="orange"

RUN pip install --upgrade pip
RUN pip install requests==2.22.0

COPY review_app_status.py /

ENTRYPOINT ["python3", "/review_app_status.py"]
