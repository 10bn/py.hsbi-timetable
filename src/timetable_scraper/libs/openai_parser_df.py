import json
import logging
import pandas as pd
from openai import OpenAI
from timetable_scraper.libs.helper_functions import load_secrets
from timetable_scraper.libs.log_config import setup_logger

# Set up the logger
setup_logger()


def openai_parser(api_key, details):
    """Parse complex multi-line timetable event details into structured JSON using OpenAI API and return a dataframe."""
    client = OpenAI(api_key=api_key)
    failure_response = {
        "course": "!!! AiParsing Failure!!!",
        "lecturer": [],
        "location": "",
        "details": "",
    }
    messages = [
        {
            "role": "system",
            "content": "You are provided with event details from a timetable, including course names, lecturers, locations, and additional details. Your task is to parse these details into a structured JSON format compliant with RFC8259, where each JSON object includes only 'course', 'lecturer', 'location', and 'details'. The 'lecturer' field should be an array containing multiple names, regardless of their position in the input. Ensure no additional fields are introduced. This is an example how the JSON should look like: [{'course': 'Programmieren in C', 'lecturer': ['P. Müller'], 'location': 'D 216', 'details': ''}, {'course': 'Praktikum 1', 'lecturer': ['Gr. B Simon Wechselstromtechnik Battermann'], 'location': 'D 221', 'details': ''}, {'course': 'Praktikum 2', 'lecturer': ['Gr. A Mayer'], 'location': '', 'details': ''}]"
        },
        {"role": "user", "content": details},
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.5,
                max_tokens=512,
                top_p=1,
            )
            structured_response = response.choices[0].message.content
            if structured_response is None:
                logging.warning("Received no content to parse, attempting retry.")
                continue  # Continue the retry loop if no response content
            structured_data = json.loads(structured_response)  # Parse the JSON here
            logging.info("Successfully parsed the response.")
            return pd.DataFrame([structured_data])  # Convert JSON data to DataFrame
        except json.JSONDecodeError as e:
            logging.warning(
                f"Retry {attempt + 1}/{max_retries}: Failed to parse JSON response. {str(e)} Trying again."
            )
        except (IndexError, KeyError, Exception) as e:
            logging.error(
                f"Error during parsing: {e}. Attempt {attempt + 1} of {max_retries}."
            )
            if attempt == max_retries - 1:
                logging.critical(
                    "Error parsing details after several attempts, please check the input format and try again."
                )
                return pd.DataFrame(
                    [failure_response]
                )  # Return failure response as DataFrame

    logging.error("Failed to obtain a valid response after multiple attempts.")
    return pd.DataFrame([failure_response])  # Return failure response as DataFrame


if __name__ == "__main__":
    # Test the function
    config = load_secrets()
    api_key = config["api_key"]
    details = "Programmieren in C, P. Wette/ D 216 Praktikum 1, Gr. B Simon Wechselstromtechnik Battermann/ D 221 Praktikum 2, Gr. A Schünemann"
    response = openai_parser(api_key, details)
    print(response)
