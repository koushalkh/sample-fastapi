# Multi-stage Docker build for FastAPI application
# Stage 1: Build stage with uv for dependency resolution
ARG BASE_IMAGE=python:3.12-slim


FROM ${BASE_IMAGE} as app-base

# Define user and group variables
ENV APP_USER=adr
ENV APP_GROUP=adrgroup
ENV APP_UID=1000
ENV APP_GID=1000

ENV PORT=8000

ENV APP_ROOT_DIR=/opt/adr

# Create app user for security
RUN groupadd -r -g ${APP_GID} ${APP_GROUP} && \
    useradd -r -u ${APP_UID} -g ${APP_GROUP} ${APP_USER}

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="${APP_ROOT_DIR}/.venv/bin:$PATH"

FROM --platform=$BUILDPLATFORM app-base as builder


RUN mkdir -p $APP_ROOT_DIR
WORKDIR $APP_ROOT_DIR

# Install uv package manager using pip
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY ./pyproject.toml ./
COPY ./uv.lock ./


# Update CA certificates and install dependencies with fallback for SSL issues
RUN apt-get update && apt-get install -y ca-certificates && \
    update-ca-certificates

RUN  uv sync --frozen --no-cache

# Stage 2: Production stage
FROM app-base as production


WORKDIR $APP_ROOT_DIR


# Copy the virtual environment from builder stage
COPY --from=builder --chown=${APP_USER}:${APP_GROUP} ${APP_ROOT_DIR}/.venv ${APP_ROOT_DIR}/.venv

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} ./app ./app

# Copy and set permissions for entrypoint script
COPY --chown=${APP_USER}:${APP_GROUP} ./docker/docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Switch to non-root user
USER ${APP_USER}

# Expose port
EXPOSE ${PORT}

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
