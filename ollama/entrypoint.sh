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

# Load the model into memory now so the first real query isn't slow. Match the
# app's request shape (chat endpoint, num_ctx 8192) so the context is allocated
# once, and keep it resident with keep_alive -1. Do this synchronously and only
# mark the model ready afterwards: the api container's healthcheck reads the
# marker, so it must not flip green until the weights are actually loaded.
echo "--> Warming up model $OLLAMA_MODEL"
if curl -s http://localhost:11434/api/chat \
  -d "{\"model\": \"$OLLAMA_MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"ping\"}], \"stream\": false, \"keep_alive\": -1, \"options\": {\"num_ctx\": 8192, \"num_predict\": 1}}" \
  > /dev/null; then
  echo "--> Model $OLLAMA_MODEL warmed up"
else
  echo "--> Warning: warmup failed; the first query will be slow" >&2
fi

# The daemon answers /api/tags the moment it starts, well before the pull or
# warmup finish, so a healthcheck on that alone would let the api start and send
# queries at a model that isn't loaded yet. This marker is what the healthcheck
# reads, and it is only written once the model is pulled AND warmed up.
touch /tmp/model-ready
echo "--> Model $OLLAMA_MODEL ready"

# Keep background daemon process running
wait $pid
