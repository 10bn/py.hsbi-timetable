import logging


def setup_logger():
    # Get the root logger
    logger = logging.getLogger()

    # Check if the logger has handlers already configured
    if not logger.handlers:
        # Configure the basic logging settings only if not already configured
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    openai_logger = logging.getLogger("openai")
    openai_logger.setLevel(logging.CRITICAL + 1)