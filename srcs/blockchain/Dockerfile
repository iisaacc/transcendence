FROM node:18

RUN apt update && \
  apt install bash

ARG   SERVICE_NAME
ENV   SERVICE_NAME=${SERVICE_NAME}

WORKDIR /usr/src/app/${SERVICE_NAME}_app

COPY  ./tools/ /tmp/

RUN chmod +x /tmp/init_hardhat.sh

EXPOSE 8545

ENTRYPOINT [ "/tmp/init_hardhat.sh" ]