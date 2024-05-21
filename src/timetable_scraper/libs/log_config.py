import logging


def setup_logger():
    # Get the root logger
    logger = logging.getLogger()

    # Configure the basic logging settings only if not already configured
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)",
    )
    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler("logfile.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )
    file_handler.setFormatter(formatter)
    # Add the file handler to the logger
    logger.addHandler(file_handler)
