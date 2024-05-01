import logging
import pandas as pd
from libs.log_config import setup_logger
from libs.helper_functions import load_secrets, save_to_csv
from libs.get_timetable_ver import extract_version
from libs.openai_parser import openai_parser
from libs.camelot_raw_pdf_data import extract_raw_data

# Set up the logger
setup_logger()


def melt_df(df):
    df = df.melt(
        id_vars=["date"], var_name="time_slot", value_name="raw_details"
    )
    return df


def get_year(pdf_path):
    version_datetime = extract_version(pdf_path)
    if version_datetime:
        return version_datetime.year
    return None


def format_date(df, current_year):
    # Define a mapping from German month abbreviations to English
    month_mapping = {
        "Jan": "Jan",
        "Feb": "Feb",
        "Mär": "Mar",
        "Apr": "Apr",
        "Mai": "May",
        "Jun": "Jun",
        "Jul": "Jul",
        "Aug": "Aug",
        "Sep": "Sep",
        "Okt": "Oct",
        "Nov": "Nov",
        "Dez": "Dec",
    }
    current_year_str = str(current_year)
    logging.info(f"Starting to format dates with the year: {current_year_str}")

    # Replace German month abbreviations with English
    df["date"] = df["date"].replace(month_mapping, regex=True)

    # Convert 'date' column to datetime format
    df["date"] = pd.to_datetime(
        df["date"].astype(str) + " " + current_year_str,
        format="%d. %b %Y",
        errors="coerce",  # Convert errors to NaT
    )

    # Check and log any entries that failed to convert
    if df["date"].isna().any():
        failed_dates = df[df["date"].isna()]["date"]
        logging.warning(
            f"Some dates were not parsed correctly and have been set to NaT. Check these entries: {failed_dates.to_list()}"
        )

    logging.info("Dates formatted successfully.")

    return df


def split_time_slot(df):
    if "time_slot" in df.columns:
        logging.info(
            "Splitting 'time_slot' column into 'start_time' and 'end_time' and replacing 'time_slot'."
        )
        try:
            # Removing 'Uhr' and splitting with keyword arguments
            time_splits = (
                df["time_slot"]
                .str.replace(" Uhr", "")
                .str.split(pat=" - ", n=1, expand=True)
            )

            # Create temporary columns for start and end times
            df["start_time"] = pd.to_datetime(
                time_splits[0].str.strip(), format="%H.%M"
            ).dt.time
            df["end_time"] = pd.to_datetime(
                time_splits[1].str.strip(), format="%H.%M"
            ).dt.time

            # Find index of 'time_slot' to insert new columns at the same position
            idx = df.columns.get_loc("time_slot")

            # Insert 'start_time' and 'end_time' before removing 'time_slot'
            df.insert(idx, "start_time", df.pop("start_time"))
            df.insert(idx + 1, "end_time", df.pop("end_time"))

            # Remove the original 'time_slot' column
            df.drop("time_slot", axis=1, inplace=True)

            logging.info(
                "Successfully replaced 'time_slot' with 'start_time' and 'end_time'."
            )
        except Exception as e:
            logging.error(f"Error processing 'time_slot': {e}")
    else:
        logging.warning(
            "The column 'time_slot' does not exist in the DataFrame. No action taken."
        )

    return df


def parse_details(raw_details, api_key):
    """Parse event details from raw details based on line count using AI parser or direct parsing."""

    # Check if raw_details is nan and return a default value if it is
    if pd.isnull(raw_details):
        return [{"course": "", "lecturer": "", "location": "", "details": ""}]

    detail_lines = raw_details.split("\n")
    if len(detail_lines) >= 2:
        return openai_parser(api_key, raw_details)
    else:
        # Parse directly based on line order
        # Check if each line exists before trying to access it
        return [
            {
                "course": detail_lines[0].strip()
                if len(detail_lines) > 0
                else "",
                "lecturer": detail_lines[1].strip()
                if len(detail_lines) > 1
                else "",
                "location": detail_lines[2].strip()
                if len(detail_lines) > 2
                else "",
                "details": detail_lines[3].strip()
                if len(detail_lines) > 3
                else "",
            }
        ]


def expand_event_details(df, api_key):
    # Define new columns in the DataFrame
    df_expanded = pd.DataFrame(
        columns=[
            "date",
            "start_time",
            "end_time",
            "course",
            "lecturer",
            "location",
            "details",
        ]
    )

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Parse the raw_details using the provided parse_details function
        parsed_details = parse_details(row["raw_details"], api_key)

        # Handle multiple events returned by the AI parser or single event from direct parsing
        for event_details in parsed_details:
            new_row = {
                "date": row["date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "course": event_details.get("course", ""),
                "lecturer": ", ".join(event_details.get("lecturer", []))
                if isinstance(event_details.get("lecturer"), list)
                else event_details.get("lecturer", ""),
                "location": event_details.get("location", ""),
                "details": event_details.get("details", ""),
            }
            # Create a DataFrame from new_row and concatenate it with df_expanded
            new_row_df = pd.DataFrame([new_row])
            df_expanded = pd.concat(
                [df_expanded, new_row_df], ignore_index=True
            )

    return df_expanded


def process_pdf_timetable(pdf_path, api_key):
    # Extract the raw data from the PDF
    df = extract_raw_data(pdf_path)
    # df = read_csv(f"{output_dir}/df_raw.csv")
    if df is None:
        logging.error("Failed to extract raw data from the PDF.")
        return

    # Get the current year from the PDF
    current_year = get_year(pdf_path)
    if current_year is None:
        logging.error("Failed to extract the current year from the PDF.")
        return

    # Process the DataFrame
    df_final = (
        df.pipe(melt_df)
        .pipe(format_date, current_year)
        .pipe(split_time_slot)
        .pipe(expand_event_details, api_key)
        .sort_values(by=["date", "start_time"])
    )
    return df_final


def main():
    secrets = load_secrets()
    pdf_path = "downloads/Stundenplan SoSe_2024_ELM 2.pdf"
    output_dir = "output"
    api_key = secrets.get("api_key")

    timetable_final = process_pdf_timetable(pdf_path, api_key)

    # Save the processed DataFrame
    save_to_csv(timetable_final, f"{output_dir}/timetable_final.csv")


if __name__ == "__main__":
    main()
