FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY taskmaster/ ./taskmaster/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

# Create default tasks directory
RUN mkdir -p /tasks

# Set environment variable for tasks directory
ENV TASKMASTER_TASKS_DIR=/tasks

VOLUME ["/tasks"]

ENTRYPOINT ["taskmaster"]
CMD ["--help"]
