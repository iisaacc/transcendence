FROM  python:3.9.20-alpine3.20

RUN   apk update && \
  apk add postgresql-client gettext && \
  rm -rf /var/cache/apk/*

RUN   pip install --upgrade pip

ARG   SERVICE_NAME
ENV   SERVICE_NAME=${SERVICE_NAME}
WORKDIR /usr/src/app/${SERVICE_NAME}_app

COPY  ./tools/ /tmp/

# Install Python dependencies specified in requirements.txt
RUN   pip install -r /tmp/requirements.txt

RUN   chmod +x /tmp/init_django.sh

RUN   mkdir -p /usr/src/app/logs

ENTRYPOINT [ "/bin/sh", "/tmp/init_django.sh" ]

