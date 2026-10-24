import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import AsyncMongoClient
import certifi
from bson import ObjectId
from datetime import datetime, timezone

# Connect to the MongoDB cluster
uri = os.getenv("MONGODB_URI")
client = AsyncMongoClient(uri, tlsCAFile=certifi.where())

# Define the database and collections
db = client.agent_db
collection = db.agent_memories   # existing — never deleted
users_collection = db.users
workspaces_collection = db.workspaces


async def init_db():
    # Existing: TTL index for memory expiry
    await collection.create_index("expiresAt", expireAfterSeconds=0)
    # New: unique email index for users
    await users_collection.create_index("email", unique=True)
    # New: index workspaces by owner and member emails
    await workspaces_collection.create_index("owner_id")
    await workspaces_collection.create_index("members.user_id")


# ─── Existing memory helpers (unchanged, CLI still works) ─────────────────────

async def insert_memory(memory_doc: dict):
    return await collection.insert_one(memory_doc)


async def search_memories(embedding: list, workspace_id: str = None):
    """Vector search. Optionally filtered to a workspace."""
    vector_search_stage = {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": embedding,
            "numCandidates": 50,
            "limit": 5,
        }
    }

    # Add pre-filter for workspace if provided
    if workspace_id:
        vector_search_stage["$vectorSearch"]["filter"] = {
            "workspace_id": {"$eq": workspace_id}
        }

    pipeline = [
        vector_search_stage,
        {
            "$project": {
                "_id": 0,
                "content": 1,
                "score": {"$meta": "vectorSearchScore"},
                "owner": 1,
                "created_at": 1,
            }
        },
    ]
    cursor = await collection.aggregate(pipeline)
    return await cursor.to_list(length=5)


async def get_memories_for_workspace(workspace_id: str, limit: int = 50):
    cursor = collection.find(
        {"workspace_id": workspace_id},
        {"_id": 1, "content": 1, "owner": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


async def delete_memory(memory_id: str):
    return await collection.delete_one({"_id": ObjectId(memory_id)})


# ─── User helpers ──────────────────────────────────────────────────────────────

async def create_user(email: str, name: str, hashed_password: str) -> dict:
    doc = {
        "email": email,
        "name": name,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_user_by_email(email: str) -> dict | None:
    return await users_collection.find_one({"email": email})


async def get_user_by_id(user_id: str) -> dict | None:
    return await users_collection.find_one({"_id": ObjectId(user_id)})


# ─── Workspace helpers ─────────────────────────────────────────────────────────

async def create_workspace(name: str, owner_id: str, owner_email: str, owner_name: str) -> dict:
    doc = {
        "name": name,
        "owner_id": owner_id,
        "members": [
            {
                "user_id": owner_id,
                "email": owner_email,
                "name": owner_name,
                "role": "owner",
            }
        ],
        "created_at": datetime.now(timezone.utc),
    }
    result = await workspaces_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_workspace(workspace_id: str) -> dict | None:
    try:
        ws = await workspaces_collection.find_one({"_id": ObjectId(workspace_id)})
        if ws:
            ws["_id"] = str(ws["_id"])
        return ws
    except Exception:
        return None


async def get_workspaces_for_user(user_id: str) -> list:
    cursor = workspaces_collection.find({"members.user_id": user_id})
    docs = await cursor.to_list(length=100)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


async def add_member_to_workspace(workspace_id: str, user_id: str, email: str, name: str, role: str) -> bool:
    result = await workspaces_collection.update_one(
        {"_id": ObjectId(workspace_id)},
        {"$push": {"members": {"user_id": user_id, "email": email, "name": name, "role": role}}}
    )
    return result.modified_count > 0


async def remove_member_from_workspace(workspace_id: str, email: str) -> bool:
    result = await workspaces_collection.update_one(
        {"_id": ObjectId(workspace_id)},
        {"$pull": {"members": {"email": email}}}
    )
    return result.modified_count > 0


async def update_member_role(workspace_id: str, email: str, new_role: str) -> bool:
    result = await workspaces_collection.update_one(
        {"_id": ObjectId(workspace_id), "members.email": email},
        {"$set": {"members.$.role": new_role}}
    )
    return result.modified_count > 0