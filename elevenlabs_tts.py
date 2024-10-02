import requests
import config
import logging

logger = logging.getLogger(__name__)

def text_to_speech(text):
    try:
        api_key = config.ELEVEN_LABS_API_KEY
        voice_id = 'cgSgspJ2msm6clMCkdW9'  # Make sure this is the correct voice ID for your use case

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Specify the multilingual model
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            logger.error("Error in text_to_speech: %s %s", response.status_code, response.text)
            return None
    except Exception as e:
        logger.error(f"Exception in text_to_speech: {str(e)}", exc_info=True)
        return None