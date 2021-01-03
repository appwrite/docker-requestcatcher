# Base
FROM python:3.6-alpine3.12 as base
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

EXPOSE 5000

CMD ["python", "app.py"]
