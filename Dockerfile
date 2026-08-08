FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/techpulse_ai ./src/techpulse_ai
RUN uv sync --frozen --no-dev

FROM ghcr.io/astral-sh/uv:python3.14-alpine

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src/techpulse_ai ./src/techpulse_ai

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "techpulse_ai.main"]
