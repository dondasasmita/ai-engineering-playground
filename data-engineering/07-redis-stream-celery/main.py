from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import redis
import asyncio
from tasks import celery_app

app = FastAPI()

# Configure Redis client
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@app.post('/start_task')
async def start_task():
    # Start the Celery task
    task = celery_app.send_task('tasks.long_running_task')
    return JSONResponse({'task_id': task.id})

@app.get('/sse/status/{task_id}')
async def stream_status(request: Request, task_id: str):
    stream_name = f"task_progress:{task_id}"
    last_id = '0-0'  # Start from the beginning of the stream

    async def event_generator():
        nonlocal last_id
        while True:
            # Check if client has disconnected
            if await request.is_disconnected():
                break

            # Read new messages from the stream
            messages = redis_client.xread({stream_name: last_id}, block=0, count=1)
            if messages:
                # messages format: [(stream_name, [(message_id, {field: value})])]
                stream, events = messages[0]
                for message_id, message_data in events:
                    last_id = message_id  # Update the last_id to the latest message
                    data = message_data.get('message')
                    yield {'data': data}

                    # Break if the task is completed
                    if data == "Task completed!":
                        return
            else:
                await asyncio.sleep(0.1)  # Sleep briefly to avoid tight loop

    return EventSourceResponse(event_generator())
