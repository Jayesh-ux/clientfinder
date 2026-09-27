"""CLIENTFINDER v3: offerings & outreach API.

Human-in-the-loop by construction: these endpoints only *generate* outreach
drafts and lists. Nothing here sends anything — sending requires an operator to
approve a draft AND use a send-enabled account via the email router.
"""

from fastapi import APIRouter, HTTPException

from .offerings import (
    offerings_list,
    outreach_for_solution,
    render_outreach,
)

router = APIRouter(prefix="/offerings", tags=["offerings"])


@router.get("")
def list_offerings():
    offerings = offerings_list()
    return {"count": len(offerings), "offerings": offerings}


@router.get("/{slug}")
def get_offering(slug: str):
    data = outreach_for_solution(slug)
    if data.get("fallback"):
        raise HTTPException(status_code=404, detail=f"unknown offering slug: {slug}")
    return data


@router.get("/{slug}/draft")
def draft_for_offering(slug: str, business: str = "this business",
                       area: str = "your area"):
    """Return a DRAFT outreach body for a solution + business. Nothing is sent."""
    data = outreach_for_solution(slug)
    if data.get("fallback"):
        raise HTTPException(status_code=404, detail=f"unknown offering slug: {slug}")
    return render_outreach(slug, business, area)