"""
Sync the Google calendar with the Emirates fixtures.
"""
import datetime
import os

import emirates_fixtures.emirates as emirates
import emirates_fixtures.google_calendar as google_calendar


def main() -> None:
    """
    Sync the Google calendar with the Emirates fixtures.
    """
    print("Syncing fixtures...")
    fixtures = emirates.get_fixtures()
    calendar = google_calendar.GoogleCalendar()
    events = calendar.get_events()
    event_summaries = [event.summary for event in events]

    for fixture in fixtures:
        summary = f"Emirates: {fixture.name}"
        print(f"Creating Google event for {summary}...")

        if summary in event_summaries:
            print(f"Event for {fixture.name} already exists and will be skipped")
            # TODO: Update event if it already exists as the date/time may have changed
            continue

        calendar.create_event(
            summary=summary,
            date_time=fixture.date_time,
            duration=datetime.timedelta(hours=2),
            attendees=[
                attendee for attendee in os.environ["ATTENDEES"].split(",") if attendee
            ],
        )

        print(f"Event for {fixture.name} created successfully")

    print("Fixtures synced!")


if __name__ == "__main__":
    main()
