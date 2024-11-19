ARG ELKF_VERSION
FROM docker.elastic.co/elasticsearch/elasticsearch:${ELKF_VERSION}

# Install expect
RUN apt-get update && apt-get install -y expect && rm -rf /var/lib/apt/lists/*

COPY elasticsearch.sh /usr/share/elasticsearch/elasticsearch.sh
RUN chmod +x /usr/share/elasticsearch/elasticsearch.sh

CMD ["sh", "-c", "/usr/local/bin/docker-entrypoint.sh & sleep 60 && /usr/share/elasticsearch/elasticsearch.sh && wait"]
