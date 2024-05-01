import logging
from webdav3.client import Client
from timetable_scraper.libs.helper_functions import load_secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def sync_timetables(output_path="./output/pdf_timetables/"):
    config = load_secrets()
    logging.info(config)
    options = {
        "webdav_hostname": config["urls"]["timetable"],
        "webdav_login": config["credentials"]["username"],
        "webdav_password": config["credentials"]["password"],
        "verbose": True,
    }
    client = Client(options)
    client.verify = True  # To not check SSL certificates (Default = True)

    try:
        files = client.list()
    except Exception as e:
        logging.error("Failed to list files: %s", e)
        return

    for i in files:
        logging.info(i)

    # Download all files to a local directory
    download_dir = "./downloads/"

    for file in files:
        if file.endswith(".pdf"):
            logging.info("Attempting to download file: %s", file)
            try:
                client.download_sync(
                    remote_path=file, local_path=download_dir + file
                )
                logging.info("Downloaded file: %s", file)
            except Exception as e:
                logging.error("Failed to download file %s: %s", file, e)
        else:
            logging.info("Skipped file: %s", file)


if __name__ == "__main__":
    sync_timetables()
    logging.info("Finished downloading timetables.")
