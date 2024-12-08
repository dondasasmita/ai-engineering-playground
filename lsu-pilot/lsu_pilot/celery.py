import os
from celery import Celery
import time

app = Celery('lsu_pilot',
             broker=os.getenv('CELERY_BROKER_URL'),
             backend=os.getenv('CELERY_RESULT_BACKEND'))

@app.task(name='demo_task')
def demo_task(message="Task completed successfully!"):
    """A simple demo task that simulates work by sleeping for 10 seconds and returns a message
    
    Args:
        message (str): Message to return after task completion
    """
    time.sleep(10)
    return f"Message after 10 seconds: {message}"

# Optional: Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
) 