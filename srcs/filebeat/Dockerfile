ARG ELKF_VERSION
FROM docker.elastic.co/beats/filebeat:${ELKF_VERSION}
USER root
RUN chmod -R 777 /usr/share/filebeat/logs
USER filebeat