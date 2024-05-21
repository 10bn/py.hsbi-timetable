import logging
import sys
from timetable_scraper.libs.helper_functions import load_secrets, save_events_to_json
from timetable_scraper.libs.update_timetable_google_api import GoogleCalendarAPI, create_all_events, delete_all_events, save_events_to_csv
from timetable_scraper.libs.process_raw_data import process_data
from timetable_scraper.libs.log_config import setup_logger


########################################################################################
#                               THIS FILE IS UNFINISHED                                #
########################################################################################

# Initialize the logger
setup_logger()
logger = logging.getLogger(__name__)

# Configuration variables
PDF_PATH = "downloads/Stundenplan SoSe_2024_ELM 2.pdf"
OUTPUT_DIR = "output"
SECRETS_FILE = "config/secrets.yaml"

def main():
    logging.info("Starting the main process.")
    
    try:
        # Load secrets
        secrets = load_secrets(SECRETS_FILE)
        if not secrets:
            logging.error("Failed to load secrets.")
            sys.exit(1)

        api_key = secrets.get("api_key")
        if not api_key:
            logging.error("API key not found in secrets.")
            sys.exit(1)

        calendar_id = secrets.get("calendar_id")
        time_zone = secrets.get("time_zone", "Europe/Berlin")
        dry_run = secrets.get("dry_run", True)

        # Process PDF timetable
        logging.info(f"Processing PDF timetable at {PDF_PATH}.")
        timetable_final = process_data(PDF_PATH, api_key)
        if timetable_final is None:
            logging.error("Failed to process PDF timetable.")
            sys.exit(1)

        # Save the processed DataFrame
        json_output_path = f"{OUTPUT_DIR}/timetable_final.json"
        save_events_to_json(timetable_final, json_output_path)
        logging.info(f"Timetable saved successfully at {json_output_path}.")

        # Synchronize with Google Calendar
        calendar_api = GoogleCalendarAPI(calendar_id, time_zone, dry_run=dry_run)

        if dry_run:
            created_events = create_all_events(calendar_api, timetable_final.to_dict('records'))
            csv_output_path = f"{OUTPUT_DIR}/dry_run_output.csv"
            save_events_to_csv(created_events, csv_output_path)
            logging.info(f"Dry run mode: Events saved to {csv_output_path}.")
        else:
            delete_all_events(calendar_api)
            create_all_events(calendar_api, timetable_final.to_dict('records'))
            logging.info("Events synchronized with Google Calendar.")

    except Exception as e:
        logging.exception("An error occurred during the main process: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
