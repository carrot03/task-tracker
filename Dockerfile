# ---- Builder stage: install dependencies into an isolated prefix ----
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Runtime stage: minimal image with only what's needed to run ----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Application code and the static frontend served by StaticFiles
COPY --chown=app:app app ./app
COPY --chown=app:app frontend ./frontend

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
