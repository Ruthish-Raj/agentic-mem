from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..auth import get_current_user
from .. import database

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "editor"  # "editor" or "viewer"


class UpdateRoleRequest(BaseModel):
    role: str


# ── helpers ────────────────────────────────────────────────────────────────────

def get_member_role(workspace: dict, user_id: str) -> str | None:
    for m in workspace.get("members", []):
        if m["user_id"] == user_id:
            return m["role"]
    return None


def require_owner(workspace: dict, user: dict):
    role = get_member_role(workspace, str(user["_id"]))
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only the workspace owner can do this")


def require_editor_or_owner(workspace: dict, user: dict):
    role = get_member_role(workspace, str(user["_id"]))
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or Owner access required")


# ── routes ─────────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_workspace(req: CreateWorkspaceRequest, current_user: dict = Depends(get_current_user)):
    ws = await database.create_workspace(
        name=req.name,
        owner_id=str(current_user["_id"]),
        owner_email=current_user["email"],
        owner_name=current_user["name"],
    )
    return ws


@router.get("")
async def list_workspaces(current_user: dict = Depends(get_current_user)):
    return await database.get_workspaces_for_user(str(current_user["_id"]))


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not get_member_role(ws, str(current_user["_id"])):
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    return ws


@router.post("/{workspace_id}/members", status_code=201)
async def invite_member(workspace_id: str, req: InviteMemberRequest, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_owner(ws, current_user)

    # Validate role
    if req.role not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="Role must be 'editor' or 'viewer'")

    # Check if already member
    if any(m["email"] == req.email for m in ws.get("members", [])):
        raise HTTPException(status_code=400, detail="User is already a member")

    # Look up the invited user
    invited = await database.get_user_by_email(req.email)
    if not invited:
        raise HTTPException(status_code=404, detail="No account found for that email. Ask them to sign up first.")

    await database.add_member_to_workspace(
        workspace_id=workspace_id,
        user_id=str(invited["_id"]),
        email=invited["email"],
        name=invited.get("name", ""),
        role=req.role,
    )
    return {"status": "Member added", "email": req.email, "role": req.role}


@router.delete("/{workspace_id}/members/{email}")
async def remove_member(workspace_id: str, email: str, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_owner(ws, current_user)

    # Cannot remove owner
    for m in ws.get("members", []):
        if m["email"] == email and m["role"] == "owner":
            raise HTTPException(status_code=400, detail="Cannot remove the workspace owner")

    removed = await database.remove_member_from_workspace(workspace_id, email)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"status": "Member removed"}


@router.patch("/{workspace_id}/members/{email}/role")
async def update_role(workspace_id: str, email: str, req: UpdateRoleRequest, current_user: dict = Depends(get_current_user)):
    ws = await database.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_owner(ws, current_user)
    if req.role not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="Role must be 'editor' or 'viewer'")
    updated = await database.update_member_role(workspace_id, email, req.role)
    if not updated:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"status": "Role updated", "email": email, "role": req.role}
