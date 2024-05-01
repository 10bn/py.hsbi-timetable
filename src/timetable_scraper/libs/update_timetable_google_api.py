# https://developers.google.com/calendar/api/v3/reference/events/get

import os
import json
import logging
from datetime import datetime, timedelta
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import yaml

#
# Constants for authentication and calendar settings
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_JSON_FILE = "token.json"
CREDENTIALS_JSON_FILE = "client_secret_727195012591-pkb8qspbipbrpuf9f956c7o6qftssdmo.apps.googleusercontent.com.json"
CALENDAR_ID = "a0fd5d4d46978655a3a840648665285da64e2a08e761c5a9b0800fd5730d2024@group.calendar.google.com"
TIME_ZONE = "Europe/Berlin"
MAX_RESULTS = 2500

# gib mir die parabel gliechung für eine parabel die durch den punkt p1(2.3,1) p(1,x) p3 (-2.3,1) geht
# f(x) = a(x - x1)(x - x2) -1


class GoogleCalendarAPI:
    def __init__(self, calendar_id, time_zone):
        self.calendar_id = calendar_id
        self.time_zone = time_zone
        self.service = self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists(TOKEN_JSON_FILE):
            creds = Credentials.from_authorized_user_file(
                TOKEN_JSON_FILE, SCOPES
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_JSON_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(TOKEN_JSON_FILE, "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    def fetch_events(self, start_date, end_date):
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
        return {
            "summary": event["summary"],
            "location": event["location"],
            "start": {"dateTime": event["start"], "timeZone": self.time_zone},
            "end": {"dateTime": event["end"], "timeZone": self.time_zone},
        }

    def create_or_update_event(self, event, event_id=None):
        event_data = self.prepare_event_data(event)
        if event_id:
            updated_event = (
                self.service.events()
                .update(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=event_data,
                )
                .execute()
            )
            logging.info(f'Event updated: {updated_event["summary"]}')
            return updated_event
        else:
            created_event = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event_data)
                .execute()
            )
            logging.info(f'Event created: {created_event["summary"]}')
            return created_event

    def delete_event(self, event_id):
        self.service.events().delete(
            calendarId=self.calendar_id, eventId=event_id
        ).execute()
        logging.info(f"Deleted event with ID: {event_id}")


def sync_calendar_with_timetable(calendar_api, local_events):
    start_date = datetime.now(pytz.timezone(TIME_ZONE))
    end_date = start_date + timedelta(days=100)
    remote_events = calendar_api.fetch_events(start_date, end_date)
    logging.info(f"Fetching events between {start_date} and {end_date}")

    remote_events_dict = {event["id"]: event for event in remote_events}
    for event in local_events:
        matched_event_id = None
        for remote_event_id, remote_event in remote_events_dict.items():
            if (
                event["summary"] == remote_event["summary"]
            ):  # Simplified matching logic
                matched_event_id = remote_event_id
                break
        if matched_event_id:
            calendar_api.create_or_update_event(
                event, event_id=matched_event_id
            )
            del remote_events_dict[matched_event_id]
        else:
            created_event = calendar_api.create_or_update_event(event)
            event["id"] = created_event[
                "id"
            ]  # Update local event with the new Google Calendar event ID

    for event_id in remote_events_dict:
        calendar_api.delete_event(event_id)
    return local_events  # Return the updated list of local events


def main():
    calendar_api = GoogleCalendarAPI(CALENDAR_ID, TIME_ZONE)
    logging.info("Authenticated with Google Calendar API.")

    with open("events.json", "r") as file:
        local_events = json.load(file)
        logging.info(f"Found {len(local_events)} events in the timetable")

    updated_local_events = sync_calendar_with_timetable(
        calendar_api, local_events
    )
    logging.info("Sync completed successfully")

    # Write the updated local events back to the local storage
    with open("output.json", "w") as file:
        json.dump(updated_local_events, file, indent=4)
    logging.info("Local storage updated with Google Calendar event IDs.")


# Uncomment the call to main() when running the script.
main()

# Delete all entries in the calendar


def delete_all_events(calendar_api):
    start_date = datetime.now(pytz.timezone(TIME_ZONE))
    end_date = start_date + timedelta(days=300)
    remote_events = calendar_api.fetch_events(start_date, end_date)
    logging.info(f"Fetching events between {start_date} and {end_date}")

    for event in remote_events:
        calendar_api.delete_event(event["id"])
    logging.info("All events deleted successfully")


# calendar_api = GoogleCalendarAPI(CALENDAR_ID, TIME_ZONE)
# delete_all_events(calendar_api)
