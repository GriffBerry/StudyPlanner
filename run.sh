#!/usr/bin/env bash
set -e

# Build the Docker image
docker build -t studyplanner:latest .

# Run the container with the .env config
docker run --rm -p 8080:8080 --env-file .env studyplanner:latest
