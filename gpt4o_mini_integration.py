import requests
import logging
import config
import json
import re

logger = logging.getLogger(__name__)

function_definitions = [
    {
        "name": "book_puja",
        "description": "Book a puja by collecting necessary details and scheduling it.",
        "parameters": {
            "type": "object",
            "properties": {
                "puja_name": {
                    "type": "string",
                    "description": "The name of the puja to be performed."
                },
                "start_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The desired start time for the puja in ISO 8601 format."
                },
                "user_name": {
                    "type": "string",
                    "description": "The name of the person booking the puja."
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "The email address of the person booking the puja."
                }
            },
            "required": ["puja_name", "start_time", "user_name", "phone_number", "location"]
        }
    }
]

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

def call_function(function_name, arguments):
    if function_name == "book_puja":
        booking_details = arguments
        event_result = create_calendar_event(booking_details)

        if event_result.get("success"):
            # Format the start time nicely for the user
            start_time_parsed = parse_future_date(booking_details['start_time'])
            formatted_time = start_time_parsed.strftime("%A, %B %d, %Y at %I:%M %p")
            return f"Puja booking confirmed for {booking_details['puja_name']} on {formatted_time} at {booking_details['location']}."
        else:
            return f"Error: {event_result.get('error')}"
    else:
        return "Function not implemented."



