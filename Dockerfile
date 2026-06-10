# Use official Python image
FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
RUN pip install --upgrade pip
RUN pip install python-dotenv langchain-google-genai langchain-google-vertexai "langchain[google,googleai]>=1.2.14" requests websockets aiohttp numexpr

# Expose ports if needed (none for websocket client)
# EXPOSE 8080

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "main.py"]
