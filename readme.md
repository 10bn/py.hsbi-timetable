## Please note that this project is a work in progress, and both the readme and the code are not yet finalized.

# Timetable Scraper and Google Calendar Integration

This project provides a Python-based solution to scrape university timetables and integrate them into Google Calendar. It allows users to automate the process of fetching timetable data, preparing event data, and updating Google Calendar with the timetable events.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Dry Run Mode](#dry-run-mode)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Timetable Scraper**: Scrapes timetable data and saves it as a JSON file.
- **Google Calendar Integration**: Authenticates with Google Calendar API and updates the calendar with the timetable events.
- **Dry Run Mode**: Allows testing without making actual changes to the Google Calendar.
- **Logging**: Provides detailed logging for monitoring and debugging.

## Installation

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. **Create and Activate a Virtual Environment**:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install the Required Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. **Google API Credentials**:
    - Obtain your Google API credentials from the Google Cloud Console.
    - Download the `client_secret.json` file and save it in the `config` directory.

2. **Setup Token Storage**:
    - Ensure you have a `config` directory in the project root.
    - The script will store the OAuth token in `config/token.json` after the first successful authentication.

3. **Update Constants**:
    - Open `update_timetable_google_api.py` and update the following constants:
        ```python
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        TOKEN_JSON_FILE = "config/token.json"
        CREDENTIALS_JSON_FILE = "config/client_secret.json"
        CALENDAR_ID_ELM2 = "your-calendar-id-elm2"
        CALENDAR_ID_ELM4 = "your-calendar-id-elm4"
        TIME_ZONE = "Europe/Berlin"
        MAX_RESULTS = 2500
        ```

## Usage

1. **Prepare Timetable Data**:
    - Ensure your timetable data is available in `output/final_events.json`.

2. **Run the Script**:
    - To update Google Calendar with the timetable events:
        ```sh
        python -u src/timetable_scraper/libs/update_timetable_google_api.py
        ```

## Dry Run Mode

- **Dry Run Mode**:
    - Use dry run mode to test the script without making actual changes to the Google Calendar.
    - In `update_timetable_google_api.py`, set `dry_run = True`:
        ```python
        if __name__ == "__main__":
            dry_run = True  # Set to False to perform actual operations
            main(dry_run)
        ```

- **Output**:
    - The script will log the actions it would have taken and save the prepared event data to `output/dry_run_output.csv`.

## Logging

- The project uses a logging configuration to provide detailed logs.
- Logs will be printed to the console and saved to a file (if configured in `log_config.py`).

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/fooBar`).
3. Commit your changes (`git commit -am 'Add some fooBar'`).
4. Push to the branch (`git push origin feature/fooBar`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
