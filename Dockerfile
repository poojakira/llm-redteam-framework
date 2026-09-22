FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REDTEAM_ENFORCEMENT_MODE=shadow

WORKDIR /app

COPY pyproject.toml README.md llm-security-config.yaml ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 redteam \
    && chown -R redteam:redteam /app
USER redteam

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

# One worker per container keeps the local in-process limiter coherent.
# Scale containers horizontally only behind a shared ingress/gateway limiter.
CMD ["uvicorn", "redteam.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]