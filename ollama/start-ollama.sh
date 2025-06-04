#!/bin/sh
set -e

#Start ollama daemon in the background
ollama serve &

# Wait for ollama to be ready
echo "Waiting for Ollama to start ..."
sleep 5

for i in {1..30}; do
    if ollama list > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Waiting for Ollama... (attempt $i/30)"
    sleep 2
done

# Pull the model
echo "Pulling gemma3:1b model..."
ollama pull gemma3:1b

echo "Ollama setup complete!"

# Keep the container running by waiting for the background process
wait