# Multi-runtime Docker container: Python 3.11 + Node.js 20 LTS (for NPX-based MCP servers)
FROM python:3.11-slim-bookworm

# Prevent Python from buffering stdout/stderr and generating pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Copy Node.js 22 LTS, npm, and npx directly from the official Node.js image
COPY --from=node:22-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-slim /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node:22-slim /usr/local/bin/npx /usr/local/bin/npx
COPY --from=node:22-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Expose port
EXPOSE 8000

# Start command: bind to 0.0.0.0 and listen on the dynamically provided Render $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers"]
