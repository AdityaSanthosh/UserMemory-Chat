"""
Memory tools for retrieving and saving user personal information as temporal facts.

This module provides async tools that the agent can use to:
- Retrieve all active facts for a user
- Retrieve historical/invalidated facts for temporal queries
- Retrieve facts for a specific entity
- Save updated facts using diff-based logic
"""

from datetime import datetime, timezone
from typing import Optional

from context import get_current_user_id
from database import get_facts_collection


async def get_all_personal_info() -> dict[str, list[str]]:
    """
    Retrieve all active personal information facts for the current user.

    Returns a dictionary mapping entity names to lists of fact content.
    Only returns currently active facts (status='active').

    Returns:
        dict[str, list[str]]: Dictionary mapping entity to list of facts.
                              Example: {"profession": ["Software engineer at Google"],
                                       "hobbies": ["playing guitar", "hiking"]}

    This tool is used by the Main Agent when the user asks questions like
    "What do you know about me?" or when the agent needs context about the user.
    """
    try:
        user_id = get_current_user_id()
        collection = get_facts_collection()

        # Query all active facts for this user
        cursor = collection.find({"user_id": user_id, "status": "active"})

        # Group facts by entity
        facts_by_entity: dict[str, list[str]] = {}
        async for doc in cursor:
            entity = doc["entity"]
            content = doc["content"]

            if entity not in facts_by_entity:
                facts_by_entity[entity] = []
            facts_by_entity[entity].append(content)

        return facts_by_entity

    except Exception as e:
        print(f"Error retrieving personal info: {e}")
        return {}


async def get_historical_facts(entity: Optional[str] = None) -> dict[str, list[dict]]:
    """
    Retrieve historical (invalidated) facts for the current user.

    This tool is used when the user asks about past information, such as:
    - "What did I enjoy before?"
    - "Where did I live before?"
    - "What was my previous job?"
    - "What hobbies did I used to have?"

    Args:
        entity: Optional entity filter (e.g., "location", "hobbies").
                If None, returns all historical facts.

    Returns:
        dict[str, list[dict]]: Dictionary mapping entity to list of historical fact details.
                               Each fact includes: content, valid_from, valid_until
                               Example: {
                                   "location": [
                                       {
                                           "content": "San Francisco",
                                           "valid_from": "2024-01-15T10:30:00Z",
                                           "valid_until": "2024-03-20T14:20:00Z"
                                       }
                                   ]
                               }
    """
    try:
        user_id = get_current_user_id()
        collection = get_facts_collection()

        # Build query
        query = {"user_id": user_id, "status": "historical"}
        if entity:
            query["entity"] = entity

        # Query historical facts, sorted by valid_until (most recent first)
        cursor = collection.find(query).sort("valid_until", -1)

        # Group facts by entity with temporal metadata
        facts_by_entity: dict[str, list[dict]] = {}
        async for doc in cursor:
            entity_name = doc["entity"]
            content = doc["content"]
            valid_from = doc.get("valid_from")
            valid_until = doc.get("valid_until")

            if entity_name not in facts_by_entity:
                facts_by_entity[entity_name] = []

            facts_by_entity[entity_name].append(
                {
                    "content": content,
                    "valid_from": valid_from.isoformat() if valid_from else None,
                    "valid_until": valid_until.isoformat() if valid_until else None,
                }
            )

        return facts_by_entity

    except Exception as e:
        print(f"Error retrieving historical facts: {e}")
        return {}


async def get_entity_facts(entity: str) -> list[str]:
    """
    Retrieve active facts for a specific entity for the current user.

    Args:
        entity: The entity name (e.g., "profession", "hobbies")

    Returns:
        list[str]: List of fact content strings for this entity

    This tool is used by the Memory Agent when resolving updates to
    determine the current state of an entity before generating new facts.
    """
    try:
        user_id = get_current_user_id()
        collection = get_facts_collection()

        # Query active facts for this entity
        cursor = collection.find(
            {"user_id": user_id, "entity": entity, "status": "active"}
        )

        # Extract content from each fact
        facts = []
        async for doc in cursor:
            facts.append(doc["content"])

        return facts

    except Exception as e:
        print(f"Error retrieving facts for entity '{entity}': {e}")
        return []


async def save_entity_facts_diff(
    entity: str,
    new_facts: list[str],
    source_text: str,
    source_timestamp: Optional[datetime] = None,
) -> str:
    """
    Save updated facts for an entity using diff-based logic.

    This function performs a differential update:
    1. Fetches current active facts for the entity
    2. Computes intersection (unchanged), removed, and new facts
    3. Preserves unchanged facts (keeps original valid_from)
    4. Invalidates removed facts (sets status='historical', valid_until=now)
    5. Inserts new facts (sets status='active', valid_from=now)

    Args:
        entity: The entity name (e.g., "profession", "hobbies")
        new_facts: List of new fact content strings
        source_text: The original user message that generated these facts
        source_timestamp: Timestamp of the source message (defaults to now)

    Returns:
        str: Confirmation message

    This tool is used by the Memory Agent after resolving the new state
    of an entity to persist changes while preserving temporal history.
    """
    try:
        user_id = get_current_user_id()
        collection = get_facts_collection()
        now = datetime.now(timezone.utc)
        source_ts = source_timestamp or now

        # Fetch current active facts
        current_facts_docs = []
        cursor = collection.find(
            {"user_id": user_id, "entity": entity, "status": "active"}
        )
        async for doc in cursor:
            current_facts_docs.append(doc)

        # Extract content for comparison
        current_facts_content = {doc["content"]: doc for doc in current_facts_docs}
        new_facts_set = set(new_facts)
        current_facts_set = set(current_facts_content.keys())

        # Compute diff
        unchanged = current_facts_set & new_facts_set  # Intersection
        removed = current_facts_set - new_facts_set  # In old but not new
        added = new_facts_set - current_facts_set  # In new but not old

        # Track operations for logging
        operations = {
            "preserved": len(unchanged),
            "invalidated": len(removed),
            "inserted": len(added),
        }

        # 1. Unchanged facts: Do nothing (preserve original valid_from)
        # (No operation needed - they stay as-is in the database)

        # 2. Removed facts: Invalidate by setting status='historical' and valid_until
        if removed:
            for fact_content in removed:
                doc = current_facts_content[fact_content]
                await collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"status": "historical", "valid_until": now}},
                )

        # 3. New facts: Insert with status='active' and valid_from=now
        if added:
            new_docs = []
            for fact_content in added:
                new_docs.append(
                    {
                        "user_id": user_id,
                        "entity": entity,
                        "content": fact_content,
                        "status": "active",
                        "valid_from": now,
                        "valid_until": None,
                        "source": {"text": source_text, "timestamp": source_ts},
                    }
                )

            await collection.insert_many(new_docs)

        print(f"Saved facts for entity '{entity}': {operations}")
        return f"Successfully updated {entity}: preserved {operations['preserved']}, invalidated {operations['invalidated']}, added {operations['inserted']} facts."

    except Exception as e:
        print(f"Error saving facts for entity '{entity}': {e}")
        return f"Error saving facts: {str(e)}"
