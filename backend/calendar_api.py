from googleapiclient.discovery import build
from oauth import get_creds
from datetime import datetime, timedelta, timezone

def list_events(days_before=7, days_after=7, max_results=25):
    service = build("calendar", "v3", credentials=get_creds())
    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=days_before)).isoformat()
    time_max = (now + timedelta(days=days_after)).isoformat()
    events_result = service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy='startTime', maxResults=max_results
    ).execute()
    return events_result.get('items', [])
