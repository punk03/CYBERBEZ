"""MongoDB connection."""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from backend.common.config import settings

# Global MongoDB client
_client: Optional[AsyncIOMotorClient] = None
_database = None


async def get_mongodb_client() -> AsyncIOMotorClient:
    """Get MongoDB client."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _client


async def get_mongodb_database():
    """Get MongoDB database."""
    global _database
    if _database is None:
        client = await get_mongodb_client()
        _database = client[settings.MONGO_DB]
    return _database


async def close_mongodb_connection():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None
