"""
MongoDB connection and initialization for user facts storage.

This module provides async MongoDB client and collection instances
for storing and retrieving temporal user facts.
"""

import os
import ssl
from typing import Optional

import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "")
DATABASE_NAME = "middleware_ai_chat"
COLLECTION_NAME = "user_facts"

# Global client and collection instances
_mongo_client: Optional[AsyncIOMotorClient] = None
_facts_collection: Optional[AsyncIOMotorCollection] = None


def get_facts_collection() -> AsyncIOMotorCollection:
    """
    Get the facts collection instance.

    Returns:
        AsyncIOMotorCollection: The user_facts collection

    Raises:
        RuntimeError: If MongoDB hasn't been initialized
    """
    if _facts_collection is None:
        raise RuntimeError(
            "MongoDB not initialized. Call init_mongo() during application startup."
        )
    return _facts_collection


async def init_mongo() -> None:
    """
    Initialize MongoDB connection and create necessary indexes.

    This function should be called during application startup.
    It creates the MongoDB client, connects to the database, and
    ensures required indexes exist for efficient querying.
    """
    global _mongo_client, _facts_collection

    if not MONGO_URI:
        print(
            "WARNING: MONGO_URI not set in environment variables. Memory features will not work."
        )
        return

    try:
        # Fix MongoDB Atlas connection string if needed
        # MongoDB Atlas requires retryWrites and w parameters
        mongo_uri = MONGO_URI
        if "mongodb+srv://" in mongo_uri and "retryWrites" not in mongo_uri:
            separator = "&" if "?" in mongo_uri else "?"
            mongo_uri = f"{mongo_uri}{separator}retryWrites=true&w=majority&tls=true"

        # Create SSL context for MongoDB Atlas compatibility
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        # Set minimum TLS version to TLS 1.2 for compatibility
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Initialize client with proper TLS/SSL settings for MongoDB Atlas
        _mongo_client = AsyncIOMotorClient(
            mongo_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
        )

        # Get database and collection
        db = _mongo_client[DATABASE_NAME]
        _facts_collection = db[COLLECTION_NAME]

        # Create indexes for efficient queries
        await _facts_collection.create_index(
            [("user_id", 1), ("entity", 1), ("status", 1)],
            name="user_entity_status_idx",
        )
        await _facts_collection.create_index(
            [("user_id", 1), ("valid_from", -1)], name="user_timestamp_idx"
        )

        print(
            f"MongoDB initialized successfully. Database: {DATABASE_NAME}, Collection: {COLLECTION_NAME}"
        )

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"⚠️  MongoDB Connection Failed")
        print(f"{'=' * 70}")
        print(f"\nError: {type(e).__name__}")
        print(f"Details: {str(e)[:200]}...")

        print(f"\n📋 TROUBLESHOOTING STEPS:")
        print(f"\n1. ✅ Check MongoDB Atlas IP Whitelist:")
        print(f"   - Go to MongoDB Atlas → Network Access")
        print(f"   - Add IP Address: 0.0.0.0/0 (allows all IPs - for testing)")
        print(f"   - Or add your current IP address")

        print(f"\n2. ✅ Verify MongoDB Atlas Cluster is Running:")
        print(f"   - Go to MongoDB Atlas Dashboard")
        print(f"   - Ensure cluster status is 'Active'")

        print(f"\n3. ✅ Check Connection String:")
        print(f"   - Format: mongodb+srv://username:password@cluster.mongodb.net/")
        print(f"   - Ensure password is URL-encoded")
        print(f"   - Current URI starts with: {MONGO_URI[:30]}...")

        print(f"\n4. ⚠️  Known Issue - OpenSSL 3.6.0 Compatibility:")
        print(f"   - Your OpenSSL version may have TLS compatibility issues")
        print(f"   - Workaround: Use MongoDB Atlas with IP whitelist configured")
        print(f"   - Or: Downgrade to Python 3.9 with older OpenSSL")

        print(f"\n5. 🔄 Try upgrading drivers:")
        print(f"   pip install --upgrade pymongo motor certifi")

        print(f"\n{'=' * 70}")
        print(f"⚡ The application will continue WITHOUT memory features")
        print(f"   Memory operations will fail silently")
        print(f"{'=' * 70}\n")

        # Don't raise - allow app to continue without memory features
        _mongo_client = None
        _facts_collection = None


async def close_mongo() -> None:
    """
    Close MongoDB connection.

    This function should be called during application shutdown.
    """
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        print("MongoDB connection closed.")
