from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from .. import database, llm
from ..auth import get_current_user
from .workspace_router import get_member_role, require_editor_or_owner

router = APIRouter(prefix="/memories", tags=["memories"])


class RememberRequest(BaseModel):
    text: str
    workspace_id: str


class AskRequest(BaseModel):
    question: str
    workspace_id: str


# ── routes ─────────────────────────────────────────────────────────────────────

@router.post("/remember")
async def remember(req: RememberRequest, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_editor_or_owner(ws, current_user)

    rule_data = await llm.extract_rule(req.text)
    if not rule_data:
        return {"status": "No rule detected"}

    rule_data["embedding"] = await llm.generate_embedding(rule_data["content"])
    rule_data["workspace_id"] = req.workspace_id
    rule_data["owner"] = current_user["email"]
    rule_data["created_at"] = datetime.now(timezone.utc)

    await database.insert_memory(rule_data)
    return {"status": "Rule saved to workspace memory", "content": rule_data["content"]}


@router.get("")
async def list_memories(workspace_id: str, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not get_member_role(ws, str(current_user["_id"])):
        raise HTTPException(status_code=403, detail="Not a workspace member")
    memories = await database.get_memories_for_workspace(workspace_id)
    return {"memories": memories}


@router.post("/ask")
async def ask(req: AskRequest, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not get_member_role(ws, str(current_user["_id"])):
        raise HTTPException(status_code=403, detail="Not a workspace member")

    query_vector = await llm.generate_embedding(req.question)
    results = await database.search_memories(query_vector, workspace_id=req.workspace_id)

    if not results:
        return {"answer": "No relevant rules found in this workspace's memory.", "sources": []}

    context_rules = [doc["content"] for doc in results]
    answer = await llm.synthesize_answer(req.question, context_rules)
    return {"answer": answer, "sources": context_rules}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, workspace_id: str, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    # Only owner can delete
    if get_member_role(ws, str(current_user["_id"])) != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete memories")
    result = await database.delete_memory(memory_id)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "Memory deleted"}
