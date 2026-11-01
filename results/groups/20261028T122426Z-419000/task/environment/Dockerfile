FROM python:3.12-slim-bookworm
WORKDIR /workspace
COPY service.py /app/service.py
COPY workspace /app/templates
COPY private /app/private
RUN mkdir -p /state /logs/verifier
CMD ["sleep", "infinity"]
