FROM python:3.13.5-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    passwd \
    screen \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN addgroup --system bowser && adduser --system --home /home/bowser --ingroup bowser bowser

ENV PYTHONPATH=/code \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    VIRTUAL_ENV=/opt/venv \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    HOME=/home/bowser \
    PATH="/opt/venv/bin:$PATH"

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Set working directory
WORKDIR /code

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY ./src/pyproject.prod.toml /code/pyproject.toml
COPY ./src/ /code/
COPY ./abis/ /code/abis/

# Set directory permissions
RUN chown -R bowser:bowser /code

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Switch to non-root user
USER bowser
