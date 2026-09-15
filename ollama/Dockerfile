FROM ollama/ollama:latest

# Install curl for the startup health check polling
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the startup script into the image
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]