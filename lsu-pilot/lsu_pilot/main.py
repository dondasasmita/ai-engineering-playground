import logging
import os

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from .prompt import CODE_PROMPT
from .functions import functions, run_function
import json
import requests

import pandas as pd
import numpy as np
from .questions import answer_question

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the CSV file
csv_path = os.path.join(current_dir + "/../", "processed", "embeddings.csv")
df = pd.read_csv(csv_path, index_col=0)
df["embeddings"] = df["embeddings"].apply(eval).apply(np.array)

ENV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

dotenv_path = os.path.join(ENV_DIR, '.env')

load_dotenv(dotenv_path)

BASE_MODEL = 'gpt-4o-mini'

if os.getenv("ENV") == "development":
    openai = OpenAI(base_url=os.getenv("LOCAL_LLM_BASE_URL"), api_key=os.getenv("LOCAL_API_KEY"))
    BASE_MODEL = os.getenv("LOCAL_MODEL")
else:
    openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

tg_bot_token = os.getenv("TG_BOT_TOKEN")

messages = [
    {"role": "system", "content": "You are a helpful assistant that answers questions."},
    # {"role": "system", "content": CODE_PROMPT}
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    messages.append({"role": "user", "content": update.message.text})

    initial_response = openai.chat.completions.create(
        model=BASE_MODEL, messages=messages, tools=functions
    )

    initial_response_message = initial_response.choices[0].message
    
    messages.append(initial_response_message)
    
    final_response = None
    
    tool_calls = initial_response_message.tool_calls
    
    if tool_calls:
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            response = run_function(name, args)
            if name == "svg_to_png_bytes":
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, photo=response
                )
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": name,
                        "content": str(response) + "Image was sent to the user, do not send the base64 string to them. Only send back 'here is the svg rendered as requested'",
                    }
                )
            elif name == "generate_image":
                  image_response = requests.get(response)
                  await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_response.content)
                  messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": name,
                        "content": "Image was generated for the user using DALL-E 3",
                    }
                )
            else:
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": name,
                        "content": str(response),
                    }
                )
            # Generate the final response
            final_response = openai.chat.completions.create(
                model=BASE_MODEL,
                messages=messages,
            )
            final_answer = final_response.choices[0].message

            # Send the final response if it exists
            if final_answer:
                messages.append(final_answer)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=final_answer.content
                )
            else:
                # Send an error message if something went wrong
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="something wrong happened, please try again",
                )
    
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=initial_response_message.content
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )

async def internal_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
      answer = answer_question(df, question=update.message.text, debug=True)
      await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

async def demo_celery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from lsu_pilot.celery import app
    
    chat_id = update.effective_chat.id
    message_text = update.message.text

    # Send the task to Celery with the chat_id
    app.send_task('demo_task', args=[chat_id, message_text])

    # Inform the user that the task has started
    await context.bot.send_message(
        chat_id=chat_id,
        text="Your task has been started and you will be notified upon completion."
    )   

async def check_task_status(task, context, chat_id):
    from asyncio import sleep
    
    while not task.ready():
        await sleep(1)  
    
    return task.get()  


if __name__ == "__main__":

    application = ApplicationBuilder().token(tg_bot_token).build()

    start_handler = CommandHandler("start", start)
    chat_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat)
    wiki_handler = CommandHandler('wiki', internal_knowledge)
    celery_handler = CommandHandler('celery', demo_celery)
    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    
    application.add_handler(wiki_handler)
    application.add_handler(celery_handler)

    application.run_polling()