"""FastAPI router for the CLIENTFINDER v3 email subsystem (draft-only default)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from service_catalog import email as email_service

router = APIRouter(prefix="/email", tags=["email"])


class AccountIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_user: Optional[str] = None
    send_enabled: bool = False
    from_name: Optional[str] = None
    from_email: Optional[str] = None


class DraftIn(BaseModel):
    lead_id: Optional[str] = None
    solution_slug: Optional[str] = None
    account_id: Optional[int] = None
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    send_after: Optional[str] = None
    tags: Optional[str] = None


class BulkDraftsIn(BaseModel):
    items: List[DraftIn]


@router.get("/accounts")
def list_accounts():
    return email_service.list_accounts()


@router.post("/accounts", status_code=201)
def create_account(payload: AccountIn):
    return email_service.create_account(payload.model_dump())


@router.post("/accounts/{account_id}/enable", status_code=200)
def enable_send(account_id: int, enabled: bool = True):
    if not email_service.set_send_enabled(account_id, enabled):
        raise HTTPException(404, "Account not found")
    return {"account_id": account_id, "send_enabled": enabled}


@router.post("/drafts", status_code=201)
def create_draft(payload: DraftIn):
    return email_service.create_draft(payload.model_dump())


@router.post("/drafts/bulk", status_code=201)
def bulk_create_drafts(payload: BulkDraftsIn):
    count = email_service.bulk_create_drafts([i.model_dump() for i in payload.items])
    return {"created": count}


@router.get("/drafts")
def list_drafts(status: str = "draft"):
    return email_service.list_drafts(status=status)


@router.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: int):
    if not email_service.approve_draft(draft_id):
        raise HTTPException(409, "Draft not found or not in status 'draft'")
    return {"draft_id": draft_id, "status": "approved"}


@router.post("/drafts/{draft_id}/send")
def send_draft(draft_id: int):
    result = email_service.send_draft(draft_id)
    if result["error"]:
        raise HTTPException(400, result["error"])
    return result


@router.get("/inbox")
def list_inbox(account_id: Optional[int] = None, limit: int = 100):
    return email_service.list_inbox(account_id=account_id, limit=limit)


@router.post("/inbox/pull")
def pull_inbox(account_id: int):
    result = email_service.fetch_inbox(account_id)
    if result["error"]:
        raise HTTPException(502, result["error"])
    return result