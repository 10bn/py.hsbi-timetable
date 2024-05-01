import re
import logging
import fitz  # PyMuPDF

from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def extract_version(pdf_path):
    """
    Extract the version date and time from the first page of a PDF.

    Args:
    pdf_path (str): Path to the PDF file.

    Returns:
    datetime or None: The extracted version as a datetime object, or None if not found.
    """
    try:
        logging.info(f"Starting to extract version from: {pdf_path}")
        pdf_document = fitz.open(pdf_path)
        first_page_text = pdf_document[0].get_text()  # type: ignore
        version_pattern = (
            r"Version:\s*(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2})\s*Uhr"
        )
        match = re.search(version_pattern, first_page_text)
        if match:
            date_version = match.group(1)  # Example: "17.04.2024"
            time_version = match.group(2)  # Example: "10:01"
            version_datetime = datetime.strptime(
                f"{date_version} {time_version}", "%d.%m.%Y %H:%M"
            )
            logging.info(f"Extracted version: {version_datetime}")
            return version_datetime
        else:
            logging.warning("Version not found in the PDF.")
            return None
    except Exception as e:
        logging.error(f"Failed to extract version due to an error: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    pdf_path = "/Users/max/github/00_HSBI_UNI/py.hsbi-timetable/downloads/Stundenplan SoSe_2024_ELM 2.pdf"
    version_datetime = extract_version(pdf_path)
    if version_datetime:
        print(f"Extracted version datetime: {version_datetime}")
    else:
        print("Failed to extract version.")
