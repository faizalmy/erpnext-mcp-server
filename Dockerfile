FROM python:3.12-slim

WORKDIR /app

# Copy everything first (hatchling needs src/ to build)
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')" || exit 1

EXPOSE 3000

# Run in HTTP mode (Streamable HTTP transport)
CMD ["python", "-m", "src.server", "--http", "--host", "0.0.0.0", "--port", "3000"]
