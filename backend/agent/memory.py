"""
Memory Agent module for processing and managing user personal information.

This module provides the Memory Agent functionality that:
1. Extracts ALL entities from user messages
2. For each entity, fetches current facts
3. Resolves new facts using LLM
4. Saves updated facts using diff-based logic

The Memory Agent operates independently from the Main Agent and handles
all memory operations, failing silently to avoid disrupting conversations.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from google.genai import Client
from google.genai.types import GenerateContentConfig

from .tools import get_entity_facts, save_entity_facts_diff

# Hardcoded list of allowed entity types for consistent naming
ALLOWED_ENTITIES = [
    "name",
    "age",
    "location",
    "profession",
    "occupation",
    "hobbies",
    "interests",
    "preferences",
    "family",
    "education",
    "goals",
    "aspirations",
    "health",
    "pets",
    "relationships",
    "skills",
    "languages",
    "dietary_preferences",
    "other",
]

# Initialize Gemini client
client = Client()


async def extract_all_entities(user_message: str) -> dict[str, list[str]]:
    """
    Extract ALL entities and their facts from a user message.

    This function uses an LLM to identify all personal information in the message
    and organize it by entity type.

    Args:
        user_message: The user's message to analyze

    Returns:
        dict[str, list[str]]: Dictionary mapping entity names to lists of facts
                              Example: {"name": ["Alex"], "location": ["San Francisco"]}
    """
    try:
        entities_list = ", ".join(ALLOWED_ENTITIES)
        prompt = f"""Extract ALL personal information from the user's message and organize it by entity type.

Allowed entity types: {entities_list}

User message: "{user_message}"

Instructions:
1. Identify ALL pieces of personal information in the message
2. Categorize each piece into the MOST SPECIFIC entity type:
   - Use 'name' for person's name ONLY
   - Use 'age' for age/birthday information
   - Use 'location' for cities, countries, places of residence
   - Use 'profession' or 'occupation' for jobs, careers, work
   - Use 'hobbies' for hobbies, activities, recreational interests
   - Use 'interests' for general interests
   - Use 'preferences' for likes/dislikes, preferences
   - Use 'family' for family-related information
   - Use 'education' for schools, degrees, studies
   - Use 'goals' for aspirations, future plans
   - Use other entity types as appropriate

3. For each entity, extract ONLY the facts relevant to that entity
4. Keep facts concise and clear
5. If no personal information is found, return an empty object

Respond with a JSON object where keys are entity names and values are arrays of facts.

Examples:

Input: "Hi, I'm Alex and I'm a software engineer from San Francisco"
Output: {{"name": ["Alex"], "profession": ["software engineer"], "location": ["San Francisco"]}}

Input: "I'm 28 years old and I love hiking and photography"
Output: {{"age": ["28 years old"], "hobbies": ["hiking", "photography"]}}

Input: "I work as a teacher in Boston and I'm learning Spanish"
Output: {{"profession": ["teacher"], "location": ["Boston"], "languages": ["learning Spanish"]}}

Input: "How's the weather?"
Output: {{}}

Respond ONLY with valid JSON. No explanation, no markdown, just the JSON object.

Response:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1000,
            ),
        )

        # Parse JSON response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines (```)
            response_text = "\n".join(
                line for line in lines if not line.startswith("```")
            )
            response_text = response_text.strip()

        # Remove "json" prefix if present
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

        entities_dict = json.loads(response_text)

        if not isinstance(entities_dict, dict):
            print(f"LLM returned non-dict response: {entities_dict}")
            return {}

        # Validate all entity names are in allowed list
        validated_dict = {}
        for entity, facts in entities_dict.items():
            if entity.lower() in ALLOWED_ENTITIES:
                # Ensure facts is a list of strings
                if isinstance(facts, list):
                    validated_dict[entity.lower()] = [str(f) for f in facts if f]

        return validated_dict

    except json.JSONDecodeError as e:
        print(f"Error parsing LLM JSON response for entity extraction: {e}")
        print(f"Response was: {response.text}")
        return {}
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return {}


async def resolve_facts_with_llm(
    entity: str, current_facts: list[str], new_facts: list[str]
) -> list[str]:
    """
    Resolve the new state of facts for an entity using LLM.

    Given current facts and new facts from a message, the LLM determines:
    - Which facts to keep (still true)
    - Which facts to update (changed)
    - Which facts to add (new information)
    - Which facts to remove (no longer true)

    Args:
        entity: The entity name (e.g., "profession", "hobbies")
        current_facts: List of current active facts for this entity
        new_facts: List of new facts extracted from the message

    Returns:
        list[str]: Complete new list of facts for this entity
    """
    try:
        # If no current facts, just return the new facts
        if not current_facts:
            return new_facts

        # If no new facts, keep current facts
        if not new_facts:
            return current_facts

        current_facts_str = json.dumps(current_facts)
        new_facts_str = json.dumps(new_facts)

        prompt = f"""You are merging facts about a user's {entity}.

Current stored facts:
{current_facts_str}

New facts from latest message:
{new_facts_str}

Your task:
Generate the complete, updated list of facts for this entity.

Instructions:
- If new facts contradict current facts, USE THE NEW FACTS (they are more recent)
- If new facts add information, ADD them to the list
- If new facts repeat existing information, KEEP the existing facts (don't duplicate)
- Each fact should be a clear, concise statement
- Only include facts relevant to '{entity}'

Examples:
- Current: ["Lives in Boston"], New: ["Lives in New York"] → ["Lives in New York"]
- Current: ["Software engineer"], New: ["Senior software engineer"] → ["Senior software engineer"]
- Current: ["Hiking"], New: ["Photography"] → ["Hiking", "Photography"]
- Current: ["Alex"], New: ["Alex"] → ["Alex"]

Respond ONLY with a JSON array of strings representing the final facts.
Example: ["fact1", "fact2", "fact3"]

Response:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=500,
            ),
        )

        # Parse JSON response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(
                line for line in lines if not line.startswith("```")
            )
            response_text = response_text.strip()

        facts = json.loads(response_text)

        if not isinstance(facts, list):
            print(f"LLM returned non-list response: {facts}")
            return current_facts

        # Ensure all facts are strings
        facts = [str(f) for f in facts if f]

        return facts if facts else current_facts

    except json.JSONDecodeError as e:
        print(f"Error parsing LLM JSON response: {e}")
        print(f"Response was: {response.text}")
        return current_facts
    except Exception as e:
        print(f"Error resolving facts with LLM: {e}")
        return current_facts


async def process_memory_update(user_message: str) -> str:
    """
    Memory Agent entry point for processing a user message and updating memory.

    This is the main function called by the Main Agent's store_personal_info tool.
    It orchestrates the entire memory update flow:
    1. Extract ALL entities and their facts from the message
    2. For each entity:
       a. Fetch current active facts
       b. Resolve new state with LLM
       c. Save the diff to the database

    The function fails silently on errors to avoid disrupting user conversation.

    Args:
        user_message: The user's message containing personal information

    Returns:
        str: Confirmation message (generic on error to fail silently)
    """
    try:
        # Step 1: Extract ALL entities from the message
        print(f"\n🔍 Processing message: {user_message[:100]}...")
        entities_with_facts = await extract_all_entities(user_message)

        if not entities_with_facts:
            print(f"No entities detected in message: {user_message}")
            return "Information noted."

        print(f"📊 Extracted entities: {list(entities_with_facts.keys())}")

        timestamp = datetime.now(timezone.utc)
        processed_count = 0

        # Step 2: Process each entity separately
        for entity, new_facts in entities_with_facts.items():
            try:
                print(f"\n  🔹 Processing entity: {entity}")
                print(f"     New facts from message: {new_facts}")

                # Fetch current facts for this entity
                current_facts = await get_entity_facts(entity)
                print(f"     Current facts in DB: {current_facts}")

                # Resolve the final state
                resolved_facts = await resolve_facts_with_llm(
                    entity, current_facts, new_facts
                )
                print(f"     Resolved final facts: {resolved_facts}")

                # Save diff to database
                result = await save_entity_facts_diff(
                    entity=entity,
                    new_facts=resolved_facts,
                    source_text=user_message,
                    source_timestamp=timestamp,
                )
                print(f"✅ {result}")
                processed_count += 1

            except Exception as e:
                # Log error but continue with other entities
                print(f"     ❌ Error processing entity '{entity}': {e}")
                continue

        if processed_count > 0:
            print(
                f"\n✅ Successfully processed {processed_count}/{len(entities_with_facts)} entities"
            )
            return f"Information stored successfully ({processed_count} categories updated)."
        else:
            print(f"\n⚠️  No entities were successfully processed")
            return "Information noted."

    except Exception as e:
        # Fail silently - don't disrupt conversation
        print(f"❌ Error in process_memory_update: {e}")
        import traceback

        traceback.print_exc()
        return "Information noted."
