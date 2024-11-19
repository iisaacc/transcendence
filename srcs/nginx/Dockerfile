FROM  nginx:1.27.1

RUN   mkdir -p /nginx/html/ /etc/nginx/ssl

# Generate self-signed certificates
RUN   openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/ssl/nginx.key \
  -out /etc/nginx/ssl/nginx.crt \
  -days 365 -nodes -subj "/CN=localhost"

COPY  ./tools/server-block.conf /etc/nginx/conf.d/

RUN   mkdir -p /var/log/nginx

CMD   ["nginx", "-g", "daemon off;"]
