FROM python:3

WORKDIR /app/
ADD . .

RUN pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

ENTRYPOINT ["python3", "download.py"]
