# Base
FROM python:3.11-alpine3.15@sha256:1567c44f47c8136752ee4301be2e94130a5f8e1fb7a0e737ccac28fb8f66fd0f as base
LABEL maintainer="team@appwrite.io"

# Build
FROM base as build

ENV PYTHONPATH=/root/http-request-catcher

WORKDIR /root

RUN apk --upgrade add --no-cache git \
  && git clone https://github.com/SmarterDM/http-request-catcher.git
  
WORKDIR /root/http-request-catcher

RUN pip install --no-cache-dir flask==1.1.2 -t .

# Prod
FROM base as prod

ENV PYTHONPATH=/home/catcher
RUN adduser catcher -D
USER catcher
WORKDIR /home/catcher

COPY --chown=catcher:catcher --from=build /root/http-request-catcher /home/catcher
COPY --chown=catcher:catcher app.py /home/catcher/app.py

EXPOSE 5000

STOPSIGNAL SIGINT

CMD ["python", "app.py"]
