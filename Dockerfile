FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* README.md ./
COPY grammar ./grammar
COPY src ./src
RUN uv build --wheel

FROM python:3.12-slim
WORKDIR /workspace
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl
COPY examples ./examples
ENTRYPOINT ["sipl"]
CMD ["--help"]