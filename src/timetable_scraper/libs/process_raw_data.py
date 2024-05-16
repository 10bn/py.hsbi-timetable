import pandas as pd
from timetable_scraper.libs.camelot_raw_pdf_to_df import create_df_from_pdf
from timetable_scraper.libs.log_config import setup_logger
from timetable_scraper.libs.openai_parser_df import openai_parser
from timetable_scraper.libs.helper_functions import (
    save_to_csv,
    save_events_to_json,
    load_secrets,
)

# Set up the logger
setup_logger()


########################################################################################
#                   PARSE THE RAW DETAILS IN A LIST OF DICTIONARIES                    #
########################################################################################


def process_data_with_openai_parser(df, api_key):
    def parse_details(raw_details):
        if pd.isnull(raw_details):
            return [{"course": "", "lecturer": "", "location": "", "details": ""}]
        detail_lines = raw_details.split("\n")
        if len(detail_lines) >= 2:
            return openai_parser(api_key, raw_details)
        else:
            return [
                {
                    "course": detail_lines[0].strip() if len(detail_lines) > 0 else "",
                    "lecturer": detail_lines[1].strip()
                    if len(detail_lines) > 1
                    else "",
                    "location": detail_lines[2].strip()
                    if len(detail_lines) > 2
                    else "",
                    "details": detail_lines[3].strip() if len(detail_lines) > 3 else "",
                }
            ]

    def process_row(row):
        parsed_details = parse_details(row.raw_details)
        expanded_rows = []
        for event_details in parsed_details:
            new_row = {
                "date": row.date,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "course": event_details.get("course", ""),
                "lecturer": ", ".join(event_details.get("lecturer", []))
                if isinstance(event_details.get("lecturer"), list)
                else event_details.get("lecturer", ""),
                "location": event_details.get("location", ""),
                "details": event_details.get("details", ""),
            }
            expanded_rows.append(new_row)
        return expanded_rows

    expanded_rows = []
    for _, row in df.iterrows():
        expanded_rows.extend(process_row(row))

    return pd.DataFrame(expanded_rows)


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
    df_final = process_data_with_openai_parser(api_key, events)
    save_events_to_json(df_final, output_dir)
    print(events.head())
