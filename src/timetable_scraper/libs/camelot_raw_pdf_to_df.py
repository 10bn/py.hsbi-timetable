import logging
import os

import camelot
import pandas as pd
from timetable_scraper.libs.get_timetable_ver import extract_version
from timetable_scraper.libs.helper_functions import save_to_csv
# Set up the logger
from timetable_scraper.libs.log_config import setup_logger
setup_logger()
logger = logging.getLogger(__name__)

########################################################################################
#                      SET ENVIRONMENT VARIABLES FOR GHOSTSCRIPT                       #
########################################################################################

os.environ["PATH"] = "/opt/homebrew/bin" + os.pathsep + os.environ["PATH"]
os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/lib"

########################################################################################
#                                GET RAW DATA FROM PDF                                 #
########################################################################################


def extract_tables(pdf_path):
    try:
        logging.info(f"Starting to extract tables from: {pdf_path}")
        table_list = camelot.read_pdf(pdf_path, flavor="lattice", pages="all")
        logging.info(f"Successfully extracted {len(table_list)} tables.")
        return table_list
    except Exception as e:
        logging.error(f"Failed to extract tables: {e}")
        return None


########################################################################################
#                                    Tables to DataFrame                               #
########################################################################################


def convert_tablelist_to_dataframe(df_tables):
    # Preprocess the tables by skipping the first row for all but the first table
    dataframes = [
        table.df if i == 0 else table.df.iloc[1:]
        for i, table in enumerate(df_tables)
    ]
    # Concatenate the tables into one DataFrame and use the first row of the first table as header
    df_final = pd.concat(dataframes, ignore_index=True)
    new_header = df_final.iloc[0]  # Grab the first row for the header
    df_final = df_final[1:]  # Take the data less the header row
    df_final.columns = new_header  # Set the header row as the df header

    # Drop the first column (assuming the first column is to be dropped after setting the header)
    df_final.drop(df_final.columns[0], axis=1, inplace=True)

    # Rename the first column to 'date' and convert it to datetime
    df_final.rename(columns={df_final.columns[0]: "date"}, inplace=True)

    return df_final


########################################################################################
#             MELT THE DF TO HAVE THE COLUMNS DATE, TIME_SLOT, RAW_DETAILS             #
########################################################################################


def melt_df(df):
    df = df.melt(id_vars=["date"], var_name="time_slot", value_name="raw_details")
    return df


########################################################################################
#                    GET THE YEAR FROM THE VERSION OF THE TIMETABLE                    #
########################################################################################


def get_year(pdf_path):
    version_datetime = extract_version(pdf_path)
    if version_datetime:
        return version_datetime.year
    return None


########################################################################################
#               COVERT DATE TO DATETIME FORMAT AND ADD THE CURRENT YEAR                #
########################################################################################


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
    # save_to_csv(df, "output/format_date.csv")
    return df


########################################################################################
#                        SPLIT TIME SLOT TO START AND END TIME                         #
########################################################################################


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
    # save_to_csv(df, "output/split_time_slot.csv")
    return df


def convert_raw_event_data_to_list(df):
    # Split the raw event data into a list
    df["raw_details"] = df["raw_details"].str.split("\n")
    return df

########################################################################################
#                       CHECK FOR MULTIPLE EVENTS IN DETAILS CELL                      #
########################################################################################

def check_multievent(df):
    # Apply the modified logic to each entry in 'raw_details'
    # Using a lambda function to check if the entry is a list and its length is greater than 4
    df["multi_event"] = df['raw_details'].apply(lambda x: len(x) > 4 if isinstance(x, list) else False)

    return df


########################################################################################
#                                    ENTRY FUNCTION                                    #
########################################################################################


def create_df_from_pdf(pdf_path):
    raw_data = extract_tables(pdf_path)
    to_df = convert_tablelist_to_dataframe(raw_data)
    df = melt_df(to_df)
    # Drop all rows wher raw_details is ['']
    df = df[df["raw_details"] != ""]
    df = split_time_slot(df)
    df = convert_raw_event_data_to_list(df)
    df = format_date(df, get_year(pdf_path))
    df = df.sort_values(by=["date", "start_time"])
    df = check_multievent(df)
    save_to_csv(df, "output/create_df.csv")
    return df


if __name__ == "__main__":
    # Example usage
    pdf_path = "/Users/max/github/00_HSBI_UNI/py.hsbi-timetable/downloads/Stundenplan SoSe_2024_ELM 2.pdf"
    df = create_df_from_pdf(pdf_path)
    #print(df.head())
    save_to_csv(df, "output/create_df.csv")
