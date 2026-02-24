FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash coreutils jq \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 10003 agent
USER agent
WORKDIR /
