from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalendarAPI:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.token_path = os.path.join(self.current_dir, 'token.pickle')
        self.creds_path = os.path.join(self.current_dir, 'CalendarAPI_creds.json')
        
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.calendar_service = self.setup_google_calendar()
        #print('setup successful')

    def setup_google_calendar(self):
        """Set up Google Calendar API service"""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If credentials are not valid, refresh them or get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        # Build service with cache disabled
        try:
            service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
            return service
        except Exception as e:
            print(f"Error building service: {e}")
            return None

    def get_calendar_events(self):
        """Get today's calendar events"""
        try:
            if not self.calendar_service:
                print('calendar service not working')
                return None

            # Get today's start and end in local timezone
            today = datetime.now(datetime.now().astimezone().tzinfo)
            start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1, microseconds=-1)

            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            if not events:
                return []

            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:  # This is a datetime
                    event_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_str = event_time.strftime("%I:%M %p")
                else:  # This is an all-day event
                    time_str = 'All Day'
                
                formatted_events.append({
                    'time': time_str,
                    'title': event.get('summary', 'No Title'),
                    'type': self.determine_event_type(event)
                })

            return formatted_events

        except Exception as e:
            logger.error(f"Failed to fetch calendar events: {e}")
            return None

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

if __name__ == "__main__":
    api = CalendarAPI()
    events = api.get_calendar_events()
    print(events)