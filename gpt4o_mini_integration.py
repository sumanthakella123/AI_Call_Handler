import requests
import logging
import config
import json
import re

logger = logging.getLogger(__name__)

def generate_response_with_context(prompt, conversation_history, context=""):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.OPENAI_API_KEY}"
    }

    if context:
        conversation_history.append({"role": "assistant", "content": context})

    conversation_history.append({"role": "user", "content": prompt})

    payload = {
        "model": "gpt-4o-mini",
        "messages": conversation_history,
        "functions": function_definitions,
        "function_call": "auto",
        "max_tokens": 150
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json:
            message = response_json['choices'][0]['message']
            conversation_history.append(message)

            if message.get("function_call"):
                function_name = message["function_call"]["name"]
                arguments = json.loads(message["function_call"]["arguments"])
                logger.debug(f"Function call detected: {function_name} with arguments {arguments}")

                function_response = call_function(function_name, arguments)

                conversation_history.append({
                    "role": "function",
                    "name": function_name,
                    "content": function_response
                })

                payload = {
                    "model": "gpt-4o-mini",
                    "messages": conversation_history,
                    "max_tokens": 150
                }

                second_response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

                if second_response.status_code == 200:
                    second_response_json = second_response.json()
                    if 'choices' in second_response_json:
                        final_message = second_response_json['choices'][0]['message']
                        conversation_history.append(final_message)
                        return final_message['content']
                    else:
                        logger.error("Unexpected response structure: %s", second_response_json)
                        return "I'm sorry, I couldn't process your request."
                else:
                    logger.error("Error: %s %s", second_response.status_code, second_response.text)
                    return "I'm sorry, I'm experiencing some technical difficulties."
            else:
                return message['content']
        else:
            logger.error("Unexpected response structure: %s", response_json)
            return "I'm sorry, I couldn't process your request."
    else:
        logger.error("Error: %s %s", response.status_code, response.text)
        return "I'm sorry, I'm experiencing some technical difficulties."


