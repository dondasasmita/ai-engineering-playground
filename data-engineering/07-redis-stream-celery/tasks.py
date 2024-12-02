import time
import redis
from celery import Celery

celery_app = Celery(
    'tasks',
    broker='amqp://guest:guest@rabbitmq:5672//',
    backend='redis://redis:6379/0'
)

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@celery_app.task(bind=True)
def long_running_task(self):
    task_id = self.request.id
    stream_name = f"task_progress:{task_id}"
    total_steps = 60  # 60 steps for more granular progress
    sleep_time = 1    # 1 second per step

    for i in range(total_steps):
        time.sleep(sleep_time)
        progress = round((i + 1) / total_steps * 100)
        message = f"Task {task_id} progress: {progress}%"
        # Add progress to Redis Stream
        redis_client.xadd(stream_name, {'message': message})
    
    # Notify completion
    redis_client.xadd(stream_name, {'message': "Task completed!"})
    return 'Task completed!'
