import json
from typing import AsyncGenerator

from google.adk.runners import Runner
from google.genai import types

from ..agent import root_agent
from ..context import clear_current_user_id, set_current_user_id
from ..database import db
from .supabase_session import SupabaseSessionService

APP_NAME = "middleware-ai-chat"


class ChatService:
    """Service for managing chat sessions and streaming responses"""

    def __init__(self):
        self.session_service = SupabaseSessionService(client=db)
        self.runner = Runner(
            agent=root_agent, app_name=APP_NAME, session_service=self.session_service
        )

    def _format_sse(self, event: str, data: dict) -> str:
        """Format data as SSE event"""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def get_user_conversations(self, user_id: str) -> list[dict]:
        result = await self.session_service.list_sessions(
            app_name=APP_NAME, user_id=user_id
        )
        conversations_list = []
        for session in result.sessions:
            title = (
                session.state.get("title", "New Chat") if session.state else "New Chat"
            )
            conversations_list.append({"id": session.id, "title": title})
        return conversations_list

    async def get_conversation_messages(
        self, user_id: str, conversation_id: str
    ) -> dict | None:
        """Get a session with its message history"""
        session = await self.session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=conversation_id
        )

        if not session:
            return None

        title = session.state.get("title", "New Chat") if session.state else "New Chat"
        messages = []

        # Extract messages from events
        print(session.events)
        for event in session.events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        role = "user" if event.author == "user" else "assistant"
                        messages.append({"role": role, "content": part.text})
                        break  # Only take the first text part

        return {"id": session.id, "title": title, "messages": messages}

    async def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation and its associated events"""
        try:
            await self.session_service.delete_session(
                app_name=APP_NAME, user_id=user_id, session_id=conversation_id
            )
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    async def _generate_title(self, first_message: str) -> str:
        """Generate a short title for the conversation"""
        title = first_message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        title = title.replace("\n", " ").strip()
        return title if title else "New Chat"

    async def stream_chat(
        self, user_id: str, conversation_id: str | None, message: str
    ) -> AsyncGenerator[str, None]:
        """Stream chat response as SSE events"""
        is_new = conversation_id is None

        # Create session only for new conversations
        if is_new:
            session = await self.session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=None,
                state={"title": await self._generate_title(message)},
            )
            session_id = session.id
        else:
            session_id = conversation_id

        # Yield session info
        yield self._format_sse(
            "session", {"conversation_id": session_id, "is_new": is_new}
        )

        try:
            # Set user context for memory operations
            set_current_user_id(user_id)

            # Create user message content
            user_content = types.Content(
                role="user", parts=[types.Part.from_text(text=message)]
            )

            full_response = ""

            # Run the agent and stream responses
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content,
            ):
                # Check if event has text content to stream
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and event.author != "user":
                            # Stream all text content (both partial and final)
                            yield self._format_sse("delta", {"content": part.text})
                            if event.partial:
                                # For partial events, accumulate the text
                                full_response += part.text
                            else:
                                # For non-partial events, use the full text
                                full_response = part.text

            # Send title for new conversations
            if is_new:
                title = await self._generate_title(message)
                yield self._format_sse("title", {"title": title})

            yield self._format_sse("done", {})

        except Exception as e:
            yield self._format_sse("error", {"message": str(e)})
        finally:
            # Clear user context after agent run
            clear_current_user_id()


# Global instance
chat_service = ChatService()
