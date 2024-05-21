import pandas as pd
import logging
from timetable_scraper.libs.camelot_raw_pdf_to_df import create_df_from_pdf
from timetable_scraper.libs.log_config import setup_logger
from timetable_scraper.libs.openai_parser import openai_parser
from timetable_scraper.libs.helper_functions import (
    save_to_csv,
    save_events_to_json,
    load_secrets,
)

# Set up the logger
setup_logger()
logger = logging.getLogger(__name__)

########################################################################################
#                   PARSE THE RAW DETAILS IN A LIST OF DICTIONARIES                    #
########################################################################################


def process_data(df, api_key):
    processed_events_columns = [
        "date",
        "start_time",
        "end_time",
        "course",
        "lecturer",
        "location",
        "details",
    ]
    processed_events = []

    for _, row in df.iterrows():
        raw_details = row["raw_details"]
        logger.info(f"Processing row: {row.to_dict()}")
        if row["multi_event"]:
            logger.info("Detected multi-event row, invoking openai_parser.")
            details_string = ", ".join(raw_details)
            parsed_events = openai_parser(api_key, details_string)
            logger.info(f"Parsed events: {parsed_events}")
            if isinstance(parsed_events, list):  # Ensure parsed_events is a list
                for event in parsed_events:
                    if isinstance(event, dict):  # Ensure each event is a dictionary
                        processed_event = {
                            "date": row["date"],
                            "start_time": row["start_time"],
                            "end_time": row["end_time"],
                            "course": event.get("course", ""),
                            "lecturer": event.get("lecturer", []),
                            "location": event.get("location", ""),
                            "details": event.get("details", ""),
                        }
                        processed_events.append(processed_event)
                        logger.info(f"Added parsed event: {processed_event}")
            else:
                logger.warning(f"Parsed events is not a list: {parsed_events}")
        else:
            # event = {
            #     "date": row["date"],
            #     "start_time": row["start_time"],
            #     "end_time": row["end_time"],
            #     "course": raw_details[0],
            #     "lecturer": [raw_details[1]],
            #     "location": raw_details[2],
            #     "details": raw_details[3] if len(raw_details) > 3 else "",
            # }
            event = {
                "date": row["date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "course": raw_details[0] if len(raw_details) > 0 else "Unknown Course",
                "lecturer": [raw_details[1]]
                if len(raw_details) > 1
                else ["Unknown Lecturer"],
                "location": raw_details[2]
                if len(raw_details) > 2
                else "Unknown Location",
                "details": raw_details[3] if len(raw_details) > 3 else "",
            }

            processed_events.append(event)
            logger.info(f"Added single event: {event}")

    processed_df = pd.DataFrame(processed_events, columns=processed_events_columns)
    logger.info("Completed processing all rows.")
    return processed_df


if __name__ == "__main__":
    secrets = load_secrets()
    pdf_path = "downloads/Stundenplan SoSe_2024_ELM 4.pdf"
    api_key = secrets.get("api_key")
    logger.info("Starting PDF to DataFrame conversion.")
    events = create_df_from_pdf(pdf_path)
    logger.info("PDF conversion completed. Starting data processing.")
    df_final = process_data(events, api_key)
    logger.info("Data processing completed. Saving to JSON and CSV.")
    save_events_to_json(df_final, "output/final_events.json")
    save_to_csv(df_final, "output/final_events.csv")
    logger.info("Data saved successfully.")
    print(df_final.head())
