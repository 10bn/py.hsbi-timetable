import logging
import pandas as pd
import yaml
from timetable_scraper.libs.log_config import setup_logger
# Set up the logger
setup_logger()
logger = logging.getLogger(__name__)


def read_csv(input_path):
    try:
        df = pd.read_csv(input_path)
        logging.info(f"Successfully read data from: {input_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to read data from {input_path}: {e}")
        return None


def save_to_csv(df, output_path):
    try:
        df.to_csv(output_path, index=False)
        logging.info(f"Saved processed data to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to save data to {output_path}: {e}")


def load_secrets(filename="config/secrets.yaml"):
    """Load secrets from a YAML file."""
    with open(filename, "r") as file:
        # Load the YAML file
        secrets = yaml.safe_load(file)
    return secrets

def save_events_to_json(df, output_path):
    """Save the extracted events to a JSON file."""
    try:
        df.to_json(output_path, orient="records", lines=False)
        logging.info(f"Successfully saved DataFrame to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save DataFrame to JSON: {e}")


if __name__ == "__main__":
    # Example usage
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    output_path = "./output/test_data.csv"
    save_to_csv(df, output_path)
    secrets = load_secrets()
    print(secrets)
