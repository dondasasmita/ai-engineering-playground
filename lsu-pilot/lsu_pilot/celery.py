import time
import os
from celery import Celery
from dotenv import load_dotenv
import asyncio
import logging
from telegram import Bot

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

dotenv_path = os.path.join(BASE_DIR, '.env')

load_dotenv(dotenv_path)

broker_url = os.environ.get('CELERY_BROKER_URL')
backend_url = os.environ.get('CELERY_RESULT_BACKEND')
telegram_bot_token = os.environ.get('TG_BOT_TOKEN')

app = Celery('lsu_pilot', broker=broker_url, backend=backend_url)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.task(name='demo_task')
def demo_task(chat_id, message):
    """A simple demo task that simulates work by sleeping for 10 seconds and returns a message
    
    Args:
        message (str): Message to return after task completion
    """
    try:
        # Simulate work
        time.sleep(10)
        
        result_message = f"Task completed: {message}"
        
        # Define async function to send message
        async def send_message():
            bot = Bot(token=telegram_bot_token)
            await bot.send_message(chat_id=chat_id, text=result_message)
        
        # Run the async function
        asyncio.run(send_message())

        logger.info(f"Message sent to chat {chat_id}")
        return result_message

    except Exception as e:
        error_msg = f"Failed to send message: {str(e)}"
        logger.error(error_msg)
        raise


# Optional: Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
) 