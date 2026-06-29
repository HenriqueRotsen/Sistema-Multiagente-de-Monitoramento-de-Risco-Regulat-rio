# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/regulatory_monitor.db

RUN groupadd --system app && \
    useradd --system --gid app --home-dir /app app && \
    mkdir -p /app/data && \
    chown -R app:app /app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app app.py main.py ./
COPY --chown=app:app src ./src
COPY --chown=app:app database ./database

USER app
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
