import logging
from timetable_scraper.libs.log_config import setup_logger
from timetable_scraper.libs.helper_functions import load_secrets
from timetable_scraper.libs.helper_functions import save_events_to_json
from timetable_scraper.libs.process_raw_data import process_pdf_timetable

setup_logger()


def main():
    logging.info("Starting the main process.")

    try:
        secrets = load_secrets()
        if not secrets:
            logging.error("Failed to load secrets.")
            return

        pdf_path = "downloads/Stundenplan SoSe_2024_ELM 2.pdf"
        output_dir = "output"
        api_key = secrets.get("api_key")

        if api_key is None:
            logging.error("API key not found in secrets.")
            return

        logging.info(f"Processing PDF timetable at {pdf_path}.")
        timetable_final = process_pdf_timetable(
            pdf_path, api_key, multi_threaded=True
        )

        if timetable_final is None:
            logging.error("Failed to process PDF timetable.")
            return

        # Save the processed DataFrame
        json_output_path = f"{output_dir}/timetable_final.json"
        save_events_to_json(timetable_final, json_output_path)
        logging.info(f"Timetable saved successfully at {json_output_path}.")

    except Exception as e:
        logging.exception("An error occurred during the main process: %s", e)


if __name__ == "__main__":
    main()
