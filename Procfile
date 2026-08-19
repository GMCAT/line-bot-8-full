web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: python -m app.workers.daily_digest_worker
