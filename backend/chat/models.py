from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ConversationInfo(BaseModel):
    conversation_id: str
    is_new: bool


class ConversationListItem(BaseModel):
    id: str
    title: str


class MessageItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[MessageItem]
