import uuid
from datetime import datetime
from typing import Optional

from google.adk.events.event import Event
from google.adk.sessions import BaseSessionService, Session
from google.adk.sessions.base_session_service import (
    GetSessionConfig,
    ListSessionsResponse,
)
from supabase import Client


def parse_postgres_timestamp(timestamp_str: str) -> float:
    """
    Parse PostgreSQL timestamp string to Unix timestamp.
    Handles timezone-aware timestamps with varying microsecond precision.

    Example: '2025-12-14T21:36:08.97237+00:00'
    """
    # Split on timezone
    if "+" in timestamp_str:
        dt_part, tz_part = timestamp_str.rsplit("+", 1)
        tz_offset = "+" + tz_part
    elif timestamp_str.endswith("Z"):
        dt_part = timestamp_str[:-1]
        tz_offset = "+00:00"
    else:
        dt_part = timestamp_str
        tz_offset = "+00:00"

    # Handle microseconds - pad or truncate to exactly 6 digits
    if "." in dt_part:
        base_dt, microseconds = dt_part.rsplit(".", 1)
        # Pad to 6 digits or truncate if longer
        microseconds = microseconds[:6].ljust(6, "0")
        dt_part = f"{base_dt}.{microseconds}"

    # Reconstruct and parse
    full_timestamp = dt_part + tz_offset
    dt = datetime.fromisoformat(full_timestamp)

    return dt.timestamp()


class SupabaseSessionService(BaseSessionService):
    """Session service implementation using Supabase."""

    def __init__(self, client: Client):
        self.client = client

    async def create_session(
        self,
        *,
        app_name: str,
        session_id: Optional[str] = None,
        user_id: str,
        state: Optional[dict] = None,
    ) -> Session:
        """Create a new session and persist it to Supabase."""
        # Ensure session_id is always a string
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            events=[],  # stored in events table
            last_update_time=datetime.now().timestamp(),
        )
        # Prepare data for insertion
        data = session.model_dump(mode="json")

        # Convert timestamp to ISO format for PostgreSQL
        if "last_update_time" in data:
            data["last_update_time"] = datetime.fromtimestamp(
                data["last_update_time"]
            ).isoformat()

        if "events" in data:
            del data["events"]

        self.client.table("sessions").insert(data).execute()

        return session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        """Retrieve a session from Supabase."""
        query = (
            self.client.table("sessions")
            .select("*")
            .eq("id", session_id)
            .eq("app_name", app_name)
            .eq("user_id", user_id)
        )

        response = query.execute()
        if not response.data:
            return None

        session_data = response.data[0]

        # Convert ISO timestamp back to Unix timestamp for Session model
        last_update_time = session_data.get("last_update_time", None)
        if isinstance(last_update_time, str):
            session_data["last_update_time"] = parse_postgres_timestamp(
                session_data["last_update_time"]
            )

        # Remove created_at as it's not part of the Session model
        if "created_at" in session_data:
            del session_data["created_at"]

        # Fetch events
        events_response = (
            self.client.table("events")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )

        events = []
        for event_row in events_response.data:
            # Assuming event_data stores the JSON of the event
            if "event_data" in event_row:
                event_obj = Event.model_validate(event_row["event_data"])
                events.append(event_obj)

        session_data["events"] = events

        return Session.model_validate(session_data)

    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        """List sessions for a user."""
        query = self.client.table("sessions").select("*").eq("app_name", app_name)
        if user_id:
            query = query.eq("user_id", user_id)

        # Order by last_update_time desc
        query = query.order("last_update_time", desc=True)

        response = query.execute()

        sessions = []
        for session_data in response.data:
            # Convert ISO timestamp back to Unix timestamp for Session model
            last_update_time = session_data.get("last_update_time", None)
            if isinstance(last_update_time, str):
                session_data["last_update_time"] = parse_postgres_timestamp(
                    session_data["last_update_time"]
                )

            # Remove created_at as it's not part of the Session model
            if "created_at" in session_data:
                del session_data["created_at"]

            # We don't fetch events for list_sessions
            session_data["events"] = []
            sessions.append(Session.model_validate(session_data))

        return ListSessionsResponse(sessions=sessions)

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Delete a session."""
        query = (
            self.client.table("sessions")
            .delete()
            .eq("id", session_id)
            .eq("app_name", app_name)
            .eq("user_id", user_id)
        )
        query.execute()

        # Events should be deleted via cascade ideally, but we can delete them manually too
        self.client.table("events").delete().eq("session_id", session_id).execute()

    async def append_event(self, session: Session, event: Event) -> Event:
        """Append an event to the session and persist it."""
        # Update in-memory session and state
        await super().append_event(session, event)

        if event.partial:
            return event

        # Persist event
        event_data = event.model_dump(mode="json")

        self.client.table("events").insert(
            {
                "session_id": session.id,
                "event_data": event_data,
                "created_at": datetime.now().isoformat(),
            }
        ).execute()

        # Update session last_update_time and state
        self.client.table("sessions").update(
            {
                "last_update_time": datetime.now().isoformat(),
                "state": session.state,
            }
        ).eq("id", session.id).execute()

        return event
