import os
import json
import logging
import csv
from datetime import datetime, timedelta
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from timetable_scraper.libs.log_config import setup_logger  # Set up the logger

logger = logging.getLogger(__name__)

# Constants for authentication and calendar settings
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_JSON_FILE = "config/token.json"
CREDENTIALS_JSON_FILE = "config/client_secret.json"
CALENDAR_ID_ELM2 = "a0fd5d4d46978655a3a840648665285da64e2a08e761c5a9b0800fd5730d2024@group.calendar.google.com"
CALENDAR_ID_ELM4 = "618b83df552bfa6b28127fa3e84c59378ebaeb272cebfcab2d0fed975d7f2369@group.calendar.google.com"

TIME_ZONE = "Europe/Berlin"
MAX_RESULTS = 2500


setup_logger()


class GoogleCalendarAPI:
    def __init__(self, calendar_id, time_zone, dry_run=False):
        self.calendar_id = calendar_id
        self.time_zone = time_zone
        self.dry_run = dry_run
        if not dry_run:
            self.service = self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists(TOKEN_JSON_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_JSON_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logging.error(f"Failed to refresh token: {e}")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_JSON_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(TOKEN_JSON_FILE, "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    def fetch_events(self, start_date, end_date):
        if self.dry_run:
            logging.info("Dry run mode: Not fetching remote events.")
            return []
        logging.info(f"Fetching events between {start_date} and {end_date}")
        events_result = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                maxResults=MAX_RESULTS,
                singleEvents=True,
                orderBy="startTime",
                timeZone=self.time_zone,
            )
            .execute()
        )
        return events_result.get("items", [])

    def prepare_event_data(self, event):
        try:
            # Parse date and combine with start and end times
            date_str = event["date"]
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(event["start_time"], "%H:%M:%S").time()
            end_time = datetime.strptime(event["end_time"], "%H:%M:%S").time()

            # Use the local time zone explicitly
            local_tz = pytz.timezone(TIME_ZONE)
            start_datetime = local_tz.localize(datetime.combine(date, start_time))
            end_datetime = local_tz.localize(datetime.combine(date, end_time))

            # Ensure lecturer is a list
            lecturer_field = event["lecturer"]
            if isinstance(lecturer_field, str):
                try:
                    lecturer_list = json.loads(lecturer_field.replace("'", '"'))
                except json.JSONDecodeError:
                    logging.error(f"Failed to decode lecturer field: {lecturer_field}")
                    lecturer_list = [lecturer_field]
            else:
                lecturer_list = lecturer_field

            # Get event details and ensure it's not None
            details = event.get("details") or ""

            # Conditionally include the comma delimiter
            summary = f"{event['course']}"
            if details:
                summary += f", {details}"

            return {
                "summary": summary,
                "location": event.get("location", ""),
                "start": {
                    "dateTime": start_datetime.isoformat(),
                    "timeZone": TIME_ZONE,
                },
                "end": {"dateTime": end_datetime.isoformat(), "timeZone": TIME_ZONE},
                "description": ", ".join(lecturer_list),
            }
        except Exception as e:
            logging.error(f"Error preparing event data: {event} - {e}")
            return None

    def create_event(self, event):
        event_data = self.prepare_event_data(event)
        if event_data:
            if self.dry_run:
                logging.info(f"Dry run mode: Prepared event data: {event_data}")
                return event_data
            else:
                created_event = (
                    self.service.events()
                    .insert(calendarId=self.calendar_id, body=event_data)
                    .execute()
                )
                logging.info(f'Event created: {created_event["summary"]}')
                return created_event
        else:
            logging.error("Failed to create event due to preparation error")

    def delete_event(self, event_id):
        if self.dry_run:
            logging.info(f"Dry run mode: Would delete event with ID: {event_id}")
        else:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()
            logging.info(f"Deleted event with ID: {event_id}")


def create_all_events(calendar_api, local_events):
    created_events = []
    for event in local_events:
        created_event = calendar_api.create_event(event)
        if created_event:
            created_events.append(created_event)
    return created_events


def delete_all_events(calendar_api):
    start_date = datetime.now(pytz.timezone(TIME_ZONE)) - timedelta(days=300)
    end_date = datetime.now(pytz.timezone(TIME_ZONE)) + timedelta(days=300)
    logging.info(f"Fetching events between {start_date} and {end_date}")

    remote_events = calendar_api.fetch_events(start_date, end_date)

    for event in remote_events:
        calendar_api.delete_event(event["id"])
    logging.info("All events deleted successfully")


def save_events_to_csv(events, filename):
    keys = events[0].keys() if events else []
    with open(filename, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(events)
    logging.info(f"Dry run mode: Events saved to {filename}")


def main(dry_run=False):
    calendar_api = GoogleCalendarAPI(CALENDAR_ID_ELM4, TIME_ZONE, dry_run)
    logging.info("Authenticated with Google Calendar API.")

    with open("output/final_events.json", "r") as file:
        try:
            local_events = json.load(file)
            logging.info(f"Found {len(local_events)} events in the timetable")
        except json.JSONDecodeError as e:
            logging.error(f"Error reading events.json: {e}")
            return

    if dry_run:
        created_events = create_all_events(calendar_api, local_events)
        save_events_to_csv(created_events, "output/dry_run_output.csv")
    else:
        delete_all_events(calendar_api)
        create_all_events(calendar_api, local_events)


if __name__ == "__main__":
    dry_run = True  # Set to False to perform actual operations
    main(dry_run)
