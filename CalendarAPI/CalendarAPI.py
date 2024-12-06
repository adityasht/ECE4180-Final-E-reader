from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import time
import os
from datetime import datetime, timedelta

import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalendarAPI:
        
    def __init__(self):
        # Initialize API
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.calendar_service = self.setup_google_calendar()
        # Initialize calendar cache
        self.calendar_cache = None
        self.last_calendar_update = None
        self.CALENDAR_UPDATE_INTERVAL = 300  # Update every 5 minutes
        print('setup successful')

    def setup_google_calendar(self):
        """Set up Google Calendar API service"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'CalendarAPI_creds.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:

            return None

    def get_calendar_events(self):
        """Get today's calendar events with caching"""
        current_time = time.time()
        
        # Return cached data if valid
        if (self.calendar_cache is not None and 
            self.last_calendar_update is not None and 
            current_time - self.last_calendar_update < self.CALENDAR_UPDATE_INTERVAL):
            return self.calendar_cache

        try:

            if not self.calendar_service:
                print('calendar service not working')
                return None

            # Get today's start and end in local timezone
            local_tz = datetime.now().astimezone().tzinfo
            today = datetime.now(local_tz)
            start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1, microseconds=-1)

            # No need for manual timezone string manipulation - let isoformat() handle it
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            formatted_events = []

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:  # This is a datetime
                    event_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_str = event_time.strftime("%I:%M %p")
                    formatted_events.append({
                        'time': time_str,
                        'title': event['summary'],
                        'type': self.determine_event_type(event)
                    })
                else:  # This is an all-day event
                    formatted_events.append({
                        'time': 'All Day',
                        'title': event['summary'],
                        'type': self.determine_event_type(event)
                    })

            self.calendar_cache = formatted_events
            self.last_calendar_update = current_time
            return formatted_events

        except Exception as e:
            logger.error(f"Failed to fetch calendar events: {str(e)}")

    def determine_event_type(self, event):
        """Determine event type based on event details"""
        title = event.get('summary', '').lower()
        description = event.get('description', '').lower()
        
        if 'meeting' in title or 'call' in title or 'sync' in title:
            return 'meeting'
        elif 'appointment' in title or 'doctor' in title or 'dentist' in title:
            return 'appointment'
        elif 'deadline' in title or 'due' in title:
            return 'deadline'
        elif 'gym' in title or 'workout' in title or 'exercise' in title:
            return 'exercise'
        elif 'lunch' in title or 'dinner' in title or 'breakfast' in title:
            return 'meal'
        else:
            return 'other'

    # Replace your existing draw_todos method with this one
if __name__ == "__main__":
    API = CalendarAPI()
    events = API.get_calendar_events()
    print(events)
        