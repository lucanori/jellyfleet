FROM python:3.12-alpine

RUN addgroup -S python && adduser -S python -G python

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=python:python . .

RUN pip install --no-cache-dir uv

USER python:python

RUN uv sync --frozen --no-dev && pip cache purge

CMD ["jellyfleet", "--help"]