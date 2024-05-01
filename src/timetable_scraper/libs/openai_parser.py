import logging
import json
from openai import OpenAI
from typing import Any
from timetable_scraper.libs.log_config import setup_logger

# Set up the logger
setup_logger()


def openai_parser(api_key, details):
    """Parse complex multi-line timetable event details into structured JSON using OpenAI API."""
    client = OpenAI(api_key=api_key)

    messages = [
        {
            "role": "system",
            "content": "You are provided with event details from a timetable, including course names, lecturers, locations, and additional details. Your task is to parse these details into a structured JSON format compliant with RFC8259, where each JSON object includes only 'course', 'lecturer', 'location', and 'details'. The 'lecturer' field should be an array containing multiple names, regardless of their position in the input. Here is a list of some existing name: ['Herth', 'Wetter', 'Battermann', 'P. Wette', 'Luhmeyer', Schünemann', 'P. Wette', 'Simon']. Ensure no additional fields are introduced. For example, if the input is 'Programmieren in C, P. Wette/ D 216 Praktikum 1, Gr. B Simon Wechselstromtechnik Battermann/ D 221 Praktikum 2, Gr. A Schünemann', the output should be [{'course': 'Programmieren in C', 'lecturer': ['P. Wette', 'Simon'], 'location': 'D 216', 'details': 'Praktikum 1, Gr. B'}, {'course': 'Wechselstromtechnik', 'lecturer': ['Battermann', 'Schünemann'], 'location': 'D 221', 'details': 'Praktikum 2, Gr. A'}]. Correctly identify and include all lecturers, even if they appear after location or detail descriptions, ensuring accurate and comprehensive data representation in each event.",
        },
        {"role": "user", "content": details},
    ]

    def load_json(s: str | None) -> Any:
        if s is None:
            return None
        return json.loads(s)

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
            structured_data = load_json(structured_response)
            logging.info("Successfully parsed the response.")
            logging.debug(
                f"Structured data: {json.dumps(structured_data, indent=4)}"
            )
            return structured_data
        except json.JSONDecodeError:
            logging.warning(
                f"Retry {attempt + 1}/{max_retries}: Failed to parse JSON response. Trying again."
            )
        except (IndexError, KeyError, Exception) as e:
            logging.error(
                f"Error during parsing: {e}. Attempt {attempt + 1} of {max_retries}."
            )
            if attempt == max_retries - 1:
                logging.critical(
                    "Error parsing details after several attempts, please check the input format and try again."
                )
                return "Error parsing details after several attempts, please check the input format and try again."

    logging.error("Failed to obtain a valid response after multiple attempts.")
    return "Failed to obtain a valid response after multiple attempts."
