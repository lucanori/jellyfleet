FROM python:3.12-alpine

RUN addgroup -g 65534 -S jellyfleet && adduser -u 65534 -S jellyfleet -G jellyfleet

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev && \
    pip cache purge

COPY --chown=jellyfleet:jellyfleet . .

RUN uv sync --frozen --no-dev

USER jellyfleet:jellyfleet

CMD ["uv", "run", "python", "-c", "print('jellyfleet CLI placeholder')"]