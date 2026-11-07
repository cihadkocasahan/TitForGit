FROM python:3.11-alpine

LABEL maintainer="Cihad KOCAŞAHAN <https://github.com/cihadkocasahan>"
LABEL description="GitPulse - Autonomous GitHub Community & Growth Engine"

WORKDIR /app

# Zero external pip packages needed! Pure Python stdlib.
COPY gitpulse.py /app/gitpulse.py

ENV PYTHONUNBUFFERED=1
ENV GITPULSE_STATE_FILE=/data/gitpulse_state.json
ENV RUN_MODE=daemon
ENV INTERVAL_SECONDS=3600

VOLUME ["/data"]

CMD ["python3", "/app/gitpulse.py"]
