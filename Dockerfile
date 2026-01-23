# ============================================================================
# DriftWatch Dockerfile - Multi-Stage Build
# ============================================================================
# Stage 1: Builder - Install dependencies
# Stage 2: Runtime - Minimal image with application
# ============================================================================

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy dependency specifications
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir great-expectations>=1.10.0 pandas>=2.3.3 pyyaml>=6.0.3 scipy>=1.17.0

# ============================================================================
# Stage 2: Runtime - Minimal image with application
# ============================================================================
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r driftwatch && \
    useradd -r -g driftwatch -u 1000 driftwatch && \
    mkdir -p /app && \
    chown -R driftwatch:driftwatch /app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=driftwatch:driftwatch driftwatch/ ./driftwatch/

# Copy GX configuration structure (not uncommitted outputs)
COPY --chown=driftwatch:driftwatch gx/great_expectations.yml ./gx/great_expectations.yml
COPY --chown=driftwatch:driftwatch gx/expectations/ ./gx/expectations/
COPY --chown=driftwatch:driftwatch gx/checkpoints/ ./gx/checkpoints/
COPY --chown=driftwatch:driftwatch gx/plugins/ ./gx/plugins/
COPY --chown=driftwatch:driftwatch gx/validation_definitions/ ./gx/validation_definitions/

# Copy sample data for built-in testing
COPY --chown=driftwatch:driftwatch data/ ./data/
COPY --chown=driftwatch:driftwatch driftwatch_config.yaml ./driftwatch_config.yaml

# Copy project metadata (for installed package mode)
COPY --chown=driftwatch:driftwatch pyproject.toml ./

# Create directories for outputs (will be mounted)
RUN mkdir -p /app/gx/uncommitted/validations && \
    mkdir -p /app/gx/uncommitted/data_docs && \
    mkdir -p /app/outputs && \
    chown -R driftwatch:driftwatch /app/gx/uncommitted /app/outputs

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER driftwatch

# Set working directory for user operations
WORKDIR /app

# Health check (verify Python and imports work)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import driftwatch; import great_expectations" || exit 1

# Entry point: driftwatch CLI via python module
ENTRYPOINT ["python", "-m", "driftwatch"]

# Default command: show help
CMD ["--help"]
