import os
import pandas as pd
import camelot
import logging


# Set environment variables for Ghostscript
os.environ["PATH"] = "/opt/homebrew/bin" + os.pathsep + os.environ["PATH"]
os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/lib"


def extract_tables(pdf_path):
    try:
        logging.info(f"Starting to extract tables from: {pdf_path}")
        df_tables = camelot.read_pdf(pdf_path, flavor="lattice", pages="all")
        logging.info(f"Successfully extracted {len(df_tables)} tables.")
        return df_tables
    except Exception as e:
        logging.error(f"Failed to extract tables: {e}")
        return None


def pre_process_tables(df_tables):
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


def extract_raw_data(pdf_path):
    # Extract tables from the PDF
    tables = extract_tables(pdf_path)
    if tables is None:
        logging.error("Failed to extract tables from the PDF.")
        return None

    # Preprocess the tables
    df_final = pre_process_tables(tables)
    if df_final.empty:
        logging.error("No data was found after processing tables.")
        return None

    return df_final


if __name__ == "__main__":
    # Example usage
    pdf_path = "/Users/max/github/00_HSBI_UNI/py.hsbi-timetable/downloads/Stundenplan SoSe_2024_ELM 2.pdf"
    tables = extract_tables(pdf_path)
    if tables:
        df_final = pre_process_tables(tables)
        # Save the concatenated DataFrame to a CSV file
        df_final.to_csv("./output/df_raw.csv", index=False)
        logging.info("Saved raw data to CSV: ./df_raw.csv")
        if not df_final.empty:
            logging.info("Data successfully processed.")
        else:
            logging.warning("No data was found after processing tables.")
    else:
        logging.error("No tables were extracted from the PDF.")
