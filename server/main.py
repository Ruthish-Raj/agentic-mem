from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from . import database, llm
from .auth import decode_token
from .routers import auth_router, workspace_router, memory_router
import asyncio

# Track WebSocket clients: { workspace_id -> set(WebSocket) } + anonymous set
connected_clients: set = set()
workspace_clients: dict = {}  # workspace_id -> set of WebSocket


async def watch_changes():
    """Listen to MongoDB Change Stream and broadcast new rules."""
    async with await database.collection.watch() as stream:
        async for change in stream:
            if change["operationType"] == "insert":
                doc = change["fullDocument"]
                rule_text = doc["content"]
                ws_id = doc.get("workspace_id")

                # Broadcast to workspace-specific clients
                if ws_id and ws_id in workspace_clients:
                    dead = set()
                    for client in workspace_clients[ws_id]:
                        try:
                            await client.send_text(f"NEW_RULE:{rule_text}")
                        except Exception:
                            dead.add(client)
                    workspace_clients[ws_id] -= dead

                # Broadcast to legacy anonymous CLI listeners
                dead = set()
                for client in connected_clients:
                    try:
                        await client.send_text(f"NEW_RULE:{rule_text}")
                    except Exception:
                        dead.add(client)
                connected_clients -= dead


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    asyncio.create_task(watch_changes())
    yield


app = FastAPI(title="Agentic Memory API", lifespan=lifespan)

# ── CORS (allow React frontend on port 5173 / 3000) ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── New authenticated routers ─────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(workspace_router.router)
app.include_router(memory_router.router)


# ════════════════════════════════════════════════════════════════════════════════
# LEGACY CLI ENDPOINTS — DO NOT REMOVE (keeps `python -m cli.main` working)
# ════════════════════════════════════════════════════════════════════════════════

class PromptRequest(BaseModel):
    text: str


@app.post("/remember")
async def remember_rule(request: PromptRequest):
    """Legacy unauthenticated endpoint — used by CLI `remember` command."""
    rule_data = await llm.extract_rule(request.text)
    if rule_data:
        rule_data["embedding"] = await llm.generate_embedding(rule_data["content"])
        await database.insert_memory(rule_data)
        return {"status": "Rule saved to shared memory"}
    return {"status": "No rule detected"}


class LegacyAskRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask_memory(request: LegacyAskRequest):
    """Legacy unauthenticated endpoint — used by CLI `ask` command."""
    query_vector = await llm.generate_embedding(request.question)
    results = await database.search_memories(query_vector)
    if not results:
        return {"answer": "No relevant project rules found in memory."}
    context_rules = [doc["content"] for doc in results]
    final_answer = await llm.synthesize_answer(request.question, context_rules)
    return {"answer": final_answer}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None), workspace_id: str = Query(None)):
    """
    WebSocket endpoint.
    - Anonymous (no token): legacy CLI sync behavior.
    - With token + workspace_id: authenticated workspace sync for frontend.
    """
    await websocket.accept()

    # Authenticated workspace mode
    if token and workspace_id:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            ws = await database.get_workspace(workspace_id)
            if not ws or not any(m["user_id"] == user_id for m in ws.get("members", [])):
                await websocket.send_text("ERROR:Not authorized for this workspace")
                await websocket.close()
                return
        except Exception:
            await websocket.send_text("ERROR:Invalid token")
            await websocket.close()
            return

        if workspace_id not in workspace_clients:
            workspace_clients[workspace_id] = set()
        workspace_clients[workspace_id].add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            workspace_clients[workspace_id].discard(websocket)
    else:
        # Legacy anonymous CLI sync
        connected_clients.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            connected_clients.discard(websocket)