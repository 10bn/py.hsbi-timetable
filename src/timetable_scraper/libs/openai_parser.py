import json
import logging
import os
from openai import OpenAI
from timetable_scraper.libs.helper_functions import load_secrets
from timetable_scraper.libs.log_config import setup_logger

# Set up the logger
setup_logger()
logger = logging.getLogger(__name__)

def openai_parser(api_key, details):
    """Parse complex multi-line timetable event details into structured JSON using OpenAI API."""
    client = OpenAI(api_key=api_key)
    failure_response = [{
        "course": "!!! AiParsing Failure!!!",
        "lecturer": [],
        "location": "",
        "details": "",
    }]
    messages = [
        {
            "role": "system",
            "content": (
                "You are provided with event details from a timetable, including course names, lecturers, "
                "locations, and additional details. Your task is to parse these details into a structured JSON "
                "format compliant with RFC8259, where each JSON object includes only 'course', 'lecturer', 'location', "
                "and 'details'. The 'lecturer' field should be an array containing multiple names, regardless of their "
                "position in the input. Here is a list of some existing names: ['Herth', 'Wetter', 'Battermann', "
                "'P. Wette', 'Luhmeyer', 'Schünemann', 'P. Wette', 'Simon']. Ensure no additional fields are introduced. "
                "For example, if the input is 'Programmieren in C, P. Wette/ D 216 Praktikum 1, Gr. B Simon "
                "Wechselstromtechnik Battermann/ D 221 Praktikum 2, Gr. A Schünemann', the output should be "
                "[{'course': 'Programmieren in C', 'lecturer': ['P. Wette', 'Simon'], 'location': 'D 216', 'details': 'Praktikum 1, Gr. B'}, "
                "{'course': 'Wechselstromtechnik', 'lecturer': ['Battermann', 'Schünemann'], 'location': 'D 221', 'details': 'Praktikum 2, Gr. A'}]. "
                "Correctly identify and include all lecturers, even if they appear after location or detail descriptions, ensuring accurate and comprehensive "
                "data representation in each event."
            ),
        },
        {"role": "user", "content": details},
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0,
                max_tokens=512,
                top_p=1,
            )
            structured_response = response.choices[0].message.content
            if structured_response is None:
                logging.warning("Received no content to parse, attempting retry.")
                continue  # Continue the retry loop if no response content
            structured_data = json.loads(structured_response)  # Parse the JSON here
            logging.info("Successfully parsed the response.")
            if isinstance(structured_data, dict):
                return [structured_data]  # Ensure it's a list of dictionaries
            elif isinstance(structured_data, list):
                return structured_data
            else:
                logging.warning("Parsed data is not a list or dict.")
                return failure_response
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
                return failure_response

    logging.error("Failed to obtain a valid response after multiple attempts.")
    return failure_response

if __name__ == "__main__":
    # Test the function
    config = load_secrets()
    api_key = config["api_key"]
    details = "['Programmieren in C,', 'P. Wette/', 'D 216', 'Praktikum 1, Gr. B', 'Simon', 'Wechselstromtechnik', 'Battermann/', 'D 221', 'Praktikum 2, Gr. A', 'Schünemann']"
    response = openai_parser(api_key, details)

    # Ensure the output directory exists
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)

    # Define the filename for the JSON file
    json_filename = os.path.join(output_dir, "response.json")

    # Save the 'response' as a JSON file
    with open(json_filename, "w") as json_file:
        json.dump(response, json_file, indent=4)

    print(response)