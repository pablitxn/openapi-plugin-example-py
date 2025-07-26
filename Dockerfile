FROM python:3.12.1-slim-bookworm

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements (if using pip) or pyproject.toml (if using poetry)
COPY pyproject.toml poetry.lock* ./

# Install Poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Install the package in development mode
RUN poetry install --no-interaction --no-ansi

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /usr/src/app
USER appuser

# Expose port
EXPOSE 4260

# Set build argument for environment
ARG Environment=development
ENV ENV=$Environment

# Command to run the application
CMD ["uvicorn", "main:app", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "4260"]