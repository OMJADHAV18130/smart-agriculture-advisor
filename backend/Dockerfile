# Smart Agriculture Advisory - backend (FastAPI + rule engine)
FROM python:3.12-slim

WORKDIR /app

# Dependencies first so this layer caches between code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + bundled CSV dataset (dataset.py resolves data/ relative to app/).
COPY app ./app
COPY data ./data
COPY tests ./tests

ENV HOST=0.0.0.0 \
    PORT=8000 \
    ENVIRONMENT=production \
    LOG_LEVEL=info

EXPOSE 8000

CMD uvicorn app.main:app --host ${HOST} --port ${PORT} --log-level ${LOG_LEVEL}

