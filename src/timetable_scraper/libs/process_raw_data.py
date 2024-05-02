import logging

import pandas as pd
from timetable_scraper.libs.camelot_raw_pdf_to_df import create_df_from_pdf
from timetable_scraper.libs.get_timetable_ver import extract_version
from timetable_scraper.libs.helper_functions import load_secrets, save_to_csv
from timetable_scraper.libs.log_config import setup_logger
from timetable_scraper.libs.openai_parser import openai_parser
from typing import List, Dict

# Set up the logger
setup_logger()


########################################################################################
#                   PARSE THE RAW DETAILS IN A LIST OF DICTIONARIES                    #
########################################################################################


def parse_raw_details(
    api_key: str, raw_details: List[str]
) -> List[Dict[str, str]]:
    """
    Extracts timetable details from the raw details provided as a list of strings and returns a list of dictionaries.
    Each dictionary contains details for a single event in the timetable with keys:
    'course', 'lecturer', 'location', 'additional_info'.
    Usually there is only one event per raw_details, but if the list is longer than 3, it can be assumed that
    the raw details contain multiple events. In this case, we will use the openai_parser function to extract the
    details for each event.

    Args:
        api_key (str): The API key used for authorization or data retrieval.
        raw_details (List[str]): The list of raw event details to be parsed.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, each containing event details.
    """

    # Check if raw_details has more than three events to process
    if len(raw_details) > 3:
        # Use openai_parser to handle multiple events
        structured_data = openai_parser(api_key, raw_details)
        return structured_data
    # Otherwise, handle a single event
    for detail in raw_details:
        # Parse the details for each event here
        # read the 
        parts = detail.split(",")
        event = {
            "course": parts[0].strip() if len(parts) > 0 else "",
            "lecturer": parts[1].strip() if len(parts) > 1 else "",
            "location": parts[2].strip() if len(parts) > 2 else "",
            "additional_info": parts[3].strip() if len(parts) > 3 else "",
        }
        timetable.append(event)

    return timetable


# "Programmieren in C,
# P. Wette/
# D 216
# Praktikum 2, Gr. A
# Simon
# Wechselstromtechnik
# Battermann/
# D 221
# Praktikum 3, Gr. B
# Schünemann"


if __name__ == "__main__":
    secrets = load_secrets()
    pdf_path = "downloads/Stundenplan SoSe_2024_ELM 2.pdf"
    output_dir = "output"
    api_key = secrets.get("api_key")
    events = create_df_from_pdf(pdf_path)
    print(events.head())
