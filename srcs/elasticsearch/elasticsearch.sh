#!/bin/bash

cd /usr/share/elasticsearch

if [ -f ".bool_pwd_set" ]; then
    echo "Password already set"
    exit 0
fi

printf "y\n$ELASTICSEARCH_PASSWORD\n$ELASTICSEARCH_PASSWORD\nchangeme\nchangeme\n$LOGSTASH_PASSWORD\n$LOGSTASH_PASSWORD\n$KIBANA_PASSWORD\n$KIBANA_PASSWORD\nchangeme\nchangeme\nchangeme\nchangeme\nchangeme\nchangeme\n" | ./bin/elasticsearch-setup-passwords interactive

touch /usr/share/elasticsearch/.bool_pwd_set