import os
import logging
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify
import ollama
from ollama import Client
from fireworks.client import Fireworks
from werkzeug.wrappers import Request, Response

load_dotenv(find_dotenv())

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_USER_ID = os.environ["SLACK_BOT_USER_ID"]
FIREWORKS_API_KEY = os.environ["FIREWORKS_API_KEY"]
OLLAMA_URL = os.environ["OLLAMA_URL"]

app = App(token=SLACK_BOT_TOKEN)
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)
slack_client = WebClient(token=SLACK_BOT_TOKEN)

def post_message(channel, text, thread_ts=None):
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )
        logging.debug(f"Message posted: {response}")
    except SlackApiError as e:
        logging.error(f"Error posting message: {e.response['error']}")


def get_user_name(user_id):
    try:
        logging.debug(f"Fetching info for user ID: {user_id}")
        response = slack_client.users_info(user=user_id)
        user_info = response.get('user', {})
        real_name = user_info.get('real_name', 'Unknown User')
        logging.debug(f"Fetched user info: {user_info}")
        return real_name
    except SlackApiError as e:
        logging.error(f"Error fetching user info for user ID {user_id}: {e.response['error']}")
        return 'Unknown User'

def draft_message(user, message):
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant. You always respond in a friendly and professional manner. Your user's name is {user}.", 
        },
        {
            "role": "user",
            "content": f"{message}",
        }
    ]
    try: 
        ollama_client = Client(host=OLLAMA_URL)
        response = ollama_client.chat(
            model='llama3.1',
            messages=messages,
        )
        return response['message']['content']
    except Exception as e:
        try:
            print("Hit Fireworks!!!!")
            client = Fireworks(api_key=FIREWORKS_API_KEY)
            response = client.chat.completions.create(
                model="accounts/fireworks/models/llama-v3p1-8b-instruct",
                messages=messages,
                max_tokens=100 
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return "Sorry, I couldn't generate a response at the moment."

def extract_text(slack_message):
  """Extracts the text content from a Slack message, removing user mentions."""

  mention_pattern = r"<@[A-Z0-9]+>" 

  cleaned_text = re.sub(mention_pattern, "", slack_message)

  return cleaned_text.strip()
    

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    logging.debug(f"Received Slack event: {data}")

    if data.get('type') == 'url_verification':
        challenge = data.get('challenge')
        logging.info(f"Responding to challenge: {challenge}")
        return jsonify({'challenge': challenge})

    # Handle app_mention events (adjust as needed)
    if "event" in data and data["event"]["type"] == "app_mention":
        event = data['event']
        user_id = event["user"]
        user_name = get_user_name(user_id)
        text = extract_text(event["text"])
        channel = event['channel']
        timestamp = event['ts']

        mention = f"<@{SLACK_BOT_USER_ID}>"
        text = text.replace(mention, '').strip()
        response = draft_message(user_name, text)
        post_message(channel, response, timestamp)

    return jsonify({"ok": True})

@flask_app.route("/slack", methods=["GET"])
def function():
    return "OK"

def main(request):
    # Create a WSGI environment dictionary
    environ = request.environ

    def start_response(status, response_headers, exc_info=None):
        """Handles the start_response call from Flask."""
        pass 

    return flask_app(environ, start_response)