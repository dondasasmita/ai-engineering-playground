from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
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
        try:
            nonlocal last_id
            while True:
                if await request.is_disconnected():
                    break

                messages = await redis_client.xread(
                    streams={stream_name: last_id},
                    count=1,
                    block=0
                )
                
                if messages:
                    stream, events = messages[0]
                    for message_id, message_data in events:
                        last_id = message_id
                        data = message_data.get('message')
                        yield {'data': data}

                        if data == "Task completed!":
                            return
                else:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in event_generator: {e}")
        finally:
            await redis_client.close()

    return EventSourceResponse(event_generator())