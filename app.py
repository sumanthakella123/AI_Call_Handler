import time
from flask import Flask, request, session, Response
from twilio.twiml.voice_response import VoiceResponse
import config
import gpt4o_mini_integration
import uuid
import os
import asyncio
import logging
from datetime import timedelta
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a secure secret key
app.permanent_session_lifetime = timedelta(minutes=30)  # Set session lifetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for logging to a file
file_handler = logging.FileHandler('logs.txt')
file_handler.setLevel(logging.DEBUG)

# Console handler for minimal logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@app.route("/", methods=['GET'])
def index():
    return "Welcome to the Albany Hindu Temple Call Handling System"

@app.route("/voice", methods=['POST'])
def voice():
    try:
        logger.info("Received /voice request")
        start_time = time.time()
        session.clear()  # Clear session data at the start of each call

        response = VoiceResponse()
        session.permanent = True  # Ensure session is saved
        session['session_id'] = str(uuid.uuid4())
        session['conversation_history'] = conversation_history_template.copy()
        session['greeted'] = False

        session_id = session['session_id']
        initial_message = session['conversation_history'][-1]['content']
        logger.debug(f"Initial message: {initial_message}")
        audio_content = text_to_speech(initial_message)
        if audio_content:
            audio_filename = f"./audio/{session_id}_initial_message.mp3"
            with open(audio_filename, "wb") as f:
                f.write(audio_content)
            response.play(f"{request.url_root}stream_audio/{session_id}_initial_message.mp3")
        session['greeted'] = True
        response.redirect('/gather')

        logger.debug(f"Initial message handling time: {time.time() - start_time} seconds")
        
        return str(response)
    except Exception as e:
        logger.error(f"Error in /voice: {str(e)}", exc_info=True)
        response = VoiceResponse()
        response.say("An application error has occurred. Please try again later.")
        return str(response)

@app.route("/gather", methods=['POST'])
def gather():
    logger.info("Received /gather request")
    try:
        response = VoiceResponse()
        response.gather(input='speech', action='/process_speech', speechTimeout='auto')
        return str(response)
    except Exception as e:
        logger.error(f"Error in /gather: {str(e)}", exc_info=True)
        response = VoiceResponse()
        response.say("An application error has occurred. Please try again later.")
        return str(response)