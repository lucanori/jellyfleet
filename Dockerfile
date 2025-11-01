FROM python:3.12-alpine

RUN addgroup -S jellyfleet && adduser -S jellyfleet -G jellyfleet

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=jellyfleet:jellyfleet . .

RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev && \
    pip cache purge

USER jellyfleet:jellyfleet

CMD ["uv", "run", "python", "-c", "print('jellyfleet CLI placeholder')"]