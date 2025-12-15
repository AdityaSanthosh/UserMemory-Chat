"""
MongoDB models and service for user personality data
"""

import os
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field


class PersonalityEntry(BaseModel):
    """Individual entry of personal information"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, str]  # The extracted personal info
    source_message: str = ""  # The original message that contained this info


class UserPersonality(BaseModel):
    """User personality document structure"""

    user_id: str
    entries: list[PersonalityEntry] = []
    summary: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    last_summarized: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PersonalityService:
    """Service for managing user personality data in MongoDB"""

    def __init__(self):
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client.middleware_chat
        self.collection = self.db.user_personalities

    async def init_db(self):
        """Initialize database with indexes"""
        # Create index on user_id for fast lookups
        await self.collection.create_index("user_id", unique=True)

    async def get_user_personality(self, user_id: str) -> Optional[UserPersonality]:
        """Get user personality document"""
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            # Remove MongoDB's _id field
            doc.pop("_id", None)
            return UserPersonality(**doc)
        return None

    async def add_personal_info(
        self, user_id: str, info: dict[str, str], source_message: str = ""
    ) -> UserPersonality:
        """Add new personal information entry for a user"""
        entry = PersonalityEntry(data=info, source_message=source_message)

        # Try to update existing document, or create new one
        result = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {
                "$push": {"entries": entry.model_dump()},
                "$set": {"last_updated": datetime.utcnow()},
                "$setOnInsert": {"summary": "", "last_summarized": None},
            },
            upsert=True,
            return_document=True,
        )

        result.pop("_id", None)
        return UserPersonality(**result)

    async def update_summary(
        self, user_id: str, summary: str
    ) -> Optional[UserPersonality]:
        """Update the personality summary for a user"""
        result = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": {"summary": summary, "last_summarized": datetime.utcnow()}},
            return_document=True,
        )

        if result:
            result.pop("_id", None)
            return UserPersonality(**result)
        return None

    async def get_summary(self, user_id: str) -> Optional[str]:
        """Get just the summary for a user"""
        personality = await self.get_user_personality(user_id)
        return personality.summary if personality else None

    async def clear_user_data(self, user_id: str) -> bool:
        """Clear all personality data for a user"""
        result = await self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0


# Global instance
personality_service = PersonalityService()
