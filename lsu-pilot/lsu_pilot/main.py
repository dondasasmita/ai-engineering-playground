import logging
import os

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import pandas as pd
import numpy as np
from .questions import answer_question

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the CSV file
csv_path = os.path.join(current_dir + "/../", "processed", "embeddings.csv")
df = pd.read_csv(csv_path, index_col=0)
df["embeddings"] = df["embeddings"].apply(eval).apply(np.array)

load_dotenv()

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tg_bot_token = os.getenv("TG_BOT_TOKEN")

messages = [
    {"role": "system", "content": "You are a helpful assistant that answers questions."}
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    messages.append({"role": "user", "content": update.message.text})
    
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages
    )
    
    completion_answer = completion.choices[0].message
    
    messages.append(completion_answer)

    
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=completion_answer.content
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )

async def internal_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
      answer = answer_question(df, question=update.message.text, debug=True)
      await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


if __name__ == "__main__":

    application = ApplicationBuilder().token(tg_bot_token).build()

    start_handler = CommandHandler("start", start)
    chat_handler = CommandHandler("chat", chat)
    wiki_handler = CommandHandler('wiki', internal_knowledge)

    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    
    application.add_handler(wiki_handler)

    application.run_polling()