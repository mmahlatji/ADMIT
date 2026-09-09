FROM python:3.11-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

COPY . .

EXPOSE 8000
# uvicorn must bind 0.0.0.0 to be reachable through Docker's port mapping at
# all, so its own startup line always echoes that literal host back, which is
# not something a browser can open. This line gives a real, clickable one.
CMD ["sh", "-c", "echo 'Open the app at http://localhost:8000 once ready' && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
