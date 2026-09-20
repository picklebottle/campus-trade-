# Pin the exact Python version this backend was built and tested against —
# avoids the pydantic-core / Python 3.14 build failures seen on some hosts'
# default runtimes.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching on rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Most hosts (Render, Railway, Fly.io, Cloud Run) inject a $PORT env var and
# expect the app to bind to it. Falls back to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
