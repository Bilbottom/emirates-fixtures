"""
Create meetings in a calendar.
"""
from __future__ import annotations

import dataclasses
import datetime
import json

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib import flow
from googleapiclient import discovery

from emirates_fixtures.constants import CREDENTIALS_FILE, TOKEN_FILE

# https://github.com/python/typing/issues/182#issuecomment-1259412066
JSON = Json = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _as_api_datetime(date_time: datetime.datetime) -> str:
    """
    Convert a datetime to the format required by the Google Calendar API.

    :param date_time: The datetime to convert.

    :return: The datetime in the format ``%Y-%m-%dT%H:%M:%SZ``.
    """
    return date_time.strftime("%Y-%m-%dT%H:%M:%SZ")


def _post(calendar_id: str, body: JSON) -> requests.Response:
    """
    Add an event to the calendar.

    This is because the ``service.events().insert()`` method is throwing an
    error saying "Missing end time", and I can't figure out why.

    :param calendar_id: The ID of the calendar to add the event to.
    :param body: The body of the request as a JSON object.

    :return: The response from the API.
    """
    token = json.loads(TOKEN_FILE.read_text())["token"]
    endpoint = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

    return requests.post(
        url=endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body),
    )


@dataclasses.dataclass
class Event:
    """
    An event in a Google calendar.

    - https://developers.google.com/calendar/v3/reference/events#resource
    """

    _base: JSON = dataclasses.field(repr=False)
    color_id: str
    html_link: str
    summary: str
    created: datetime.datetime
    updated: datetime.datetime
    creator: User
    organizer: User
    start: Timestamp
    end: Timestamp

    @dataclasses.dataclass
    class User:
        email: str
        display_name: str

        @classmethod
        def from_dict(cls, user_json: JSON) -> Event.User:
            return cls(
                email=user_json.get("email"),
                display_name=user_json.get("displayName"),
            )

    @dataclasses.dataclass
    class Timestamp:
        date_time: datetime.datetime
        time_zone: str

        @classmethod
        def from_dict(cls, timestamp_json: JSON) -> Event.Timestamp:
            timestamp = (
                timestamp_json.get("dateTime")
                or timestamp_json.get("date") + "T00:00:00Z"
            )

            return cls(
                date_time=datetime.datetime.fromisoformat(timestamp),
                time_zone=timestamp_json.get("timeZone"),
            )

    @classmethod
    def from_dict(cls, event: JSON) -> Event:
        return cls(
            _base=event,
            color_id=event.get("colorId"),
            html_link=event.get("htmlLink"),
            summary=event.get("summary"),
            created=datetime.datetime.fromisoformat(event.get("created")),
            updated=datetime.datetime.fromisoformat(event.get("updated")),
            creator=cls.User.from_dict(event.get("creator")),
            organizer=cls.User.from_dict(event.get("organizer")),
            start=cls.Timestamp.from_dict(event.get("start")),
            end=cls.Timestamp.from_dict(event.get("end")),
        )


class GoogleCalendar:
    """
    A connector to a Google calendar.
    """

    def __init__(self) -> None:
        """
        Initialise a Google calendar connector.
        """
        self._token_file = TOKEN_FILE
        self._credentials_file = CREDENTIALS_FILE
        self._credentials = None

    def _update_credentials(self) -> None:
        """
        Update the authentication credentials.

        Uses the existing credentials if they are still valid, otherwise
        refreshes them. For credentials that don't exist, the OAuth flow is
        started to create them.
        """
        if (
            self._credentials
            and self._credentials.expired
            and self._credentials.refresh_token
        ):
            self._credentials.refresh(Request())
        else:
            flow_ = flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file=str(self._credentials_file),
                scopes=SCOPES,
            )
            self._credentials = flow_.run_local_server(port=0)

        self._token_file.write_text(self._credentials.to_json())

    @property
    def credentials(self) -> Credentials:
        """
        Get the authentication credentials for the calendar.

        :return: The authentication credentials.
        """
        if self._token_file.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self._token_file), SCOPES
            )

        if not self._credentials or not self._credentials.valid:
            self._update_credentials()

        return self._credentials

    @property
    def service(self) -> discovery.Resource:
        """
        Get the calendar service.

        :return: A Google API resource corresponding to the calendar.
        """
        return discovery.build(
            serviceName="calendar",
            version="v3",
            credentials=self.credentials,
        )

    def get_events(self) -> list[Event]:
        """
        Get the events from the calendar for the next 90 days.

        :return: A list of the events in the calendar.
        """
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=_as_api_datetime(datetime.datetime.now()),
                timeMax=_as_api_datetime(
                    datetime.datetime.now() + datetime.timedelta(days=90)
                ),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        return [Event.from_dict(event) for event in events_result.get("items", [])]

    def create_event(
        self,
        summary: str,
        date_time: datetime.datetime,
        duration: datetime.timedelta,
        attendees: list[str] = None,
    ) -> requests.Response:
        """
        Create a meeting in the calendar.

        :param summary: The event title.
        :param date_time: The start time of the event.
        :param duration: The duration of the event.
        :param attendees: The (optional) list of attendees' emails.
        """
        payload: JSON = {
            "summary": summary,
            "description": "Created by: https://github.com/Bilbottom/emirates-fixtures",
            "start": {
                "dateTime": _as_api_datetime(date_time),
                "timeZone": "Europe/London",
            },
            "end": {
                "dateTime": _as_api_datetime(date_time + duration),
                "timeZone": "Europe/London",
            },
            "colorId": "11",  # Red
        }
        if attendees:
            payload["attendees"] = [{"email": attendee} for attendee in attendees]

        # return self.service.events().insert(calendarId="primary", body=json.dumps(payload)).execute()
        return _post(calendar_id="primary", body=payload)
