FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git curl ca-certificates coreutils findutils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /
RUN useradd -m -u 10001 agent
USER agent
