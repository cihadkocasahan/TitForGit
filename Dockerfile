FROM python:3.11-alpine

LABEL maintainer="Cihad KOCAŞAHAN <https://github.com/cihadkocasahan>"
LABEL description="TitForGit - Autonomous Reciprocal GitHub Engagement Engine"

WORKDIR /app

# Zero external pip packages needed! Pure Python stdlib.
COPY titforgit.py /app/titforgit.py

ENV PYTHONUNBUFFERED=1
ENV TITFORGIT_DATA_DIR=/data
ENV RUN_MODE=server
ENV PORT=8080
ENV INTERVAL_SECONDS=3600

EXPOSE 8080
VOLUME ["/data"]

CMD ["python3", "/app/titforgit.py"]
