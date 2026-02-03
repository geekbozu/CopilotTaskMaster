FROM python:3.11-slim

WORKDIR /app

# Optional build-time version argument (derived from git tag in CI)
ARG VERSION=0.0.0
ENV TASKMASTER_VERSION=$VERSION
# Provide setuptools_scm a hint when .git is not available during build
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_COPILOTTASKMASTER=$VERSION
LABEL org.opencontainers.image.version=$VERSION

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY taskmaster/ ./taskmaster/
COPY pyproject.toml .

# Install the package in editable mode and verify the package version (helps detect build-time versioning issues)
RUN pip install --no-cache-dir -e . \
    && python -c "import taskmaster; print('taskmaster version:', taskmaster.__version__)"

# Create default tasks directory
RUN mkdir -p /tasks

# Set environment variable for tasks directory
ENV TASKMASTER_TASKS_DIR=/tasks

VOLUME ["/tasks"]

ENTRYPOINT ["taskmaster"]
CMD ["--help"]
