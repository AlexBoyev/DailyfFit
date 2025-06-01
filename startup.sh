#!/bin/sh

# Start Ollama server in background
ollama serve &

# Wait for Ollama API to become available (timeout 1500)
echo "Waiting for Ollama to start..."
timeout=2000
elapsed=0

until curl -s http://localhost:11434 > /dev/null; do
  sleep 1
  elapsed=$((elapsed + 1))
  if [ $elapsed -ge $timeout ]; then
    echo "Timeout reached waiting for Ollama to start."
    exit 1
  fi
done

echo "Ollama is ready."

# Check if tinyllama is already pulled
if ollama list | grep -q "tinyllama"; then
  echo "tinyllama already available, skipping pull."
else
  echo "Pulling tinyllama..."
  ollama pull tinyllama
fi

# Keep container alive
wait