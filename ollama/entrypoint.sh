#!/bin/bash
set -euo pipefail

# Start Ollama daemon in the background
/bin/ollama serve &
pid=$!

echo "--> Waiting for Ollama daemon to initialize..."

# Active polling check
count=0
until curl -s http://localhost:11434/api/tags > /dev/null || [ $count -eq 30 ]; do
  sleep 1
  count=$((count + 1))
done

if [ $count -eq 30 ]; then
  echo "--> Error: Ollama daemon failed to start within 30 seconds."
  exit 1
fi

# :- because set -u aborts on an unset variable before the test can run, which
# turned this check into an "unbound variable" trace instead of the message.
if [ -z "${OLLAMA_MODEL:-}" ]; then
  echo "--> Error: OLLAMA_MODEL is not set."
  exit 1
fi

echo "--> Pulling Model $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

# The daemon answers /api/tags the moment it starts, well before the pull
# finishes, so a healthcheck on that alone lets the api start and send queries
# at a model that is not there yet. This marker is what the healthcheck reads.
touch /tmp/model-ready
echo "--> Model $OLLAMA_MODEL ready"

# Load the model into memory now so the first real query isn't slow. Backgrounded
# so it can't block the daemon's `wait` below (or the api container, whose
# healthcheck reads the model-ready marker written above, not this request).
echo "--> Warming up model $OLLAMA_MODEL"
curl -s http://localhost:11434/api/generate \
  -d "{\"model\": \"$OLLAMA_MODEL\", \"prompt\": \"ping\", \"keep_alive\": -1, \"options\": {\"num_predict\": 1}}" \
  > /dev/null &

# Keep background daemon process running
wait $pid
