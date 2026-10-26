import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "sales_intel_worker",
    broker=broker_url,
    backend=result_backend
)

celery_app.conf.task_routes = {
    "app.worker.train_model": "ml-queue",
    "app.worker.process_data": "data-queue"
}

@celery_app.task(name="app.worker.train_model")
def train_model(sku: str):
    # ML pipeline execution logic here
    return f"Model trained for {sku}"
