"""FastAPI router for the CLIENTFINDER v3 catalog API."""

from fastapi import APIRouter, HTTPException

from service_catalog import repository as repo
from service_catalog.schemas import (
    CapabilityIn, CapabilityUpdate,
    EvidenceIn, EvidenceUpdate,
    SolutionIn, SolutionUpdate,
    ProblemPatternIn, ProblemPatternUpdate,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


# ---------------------------------------------------------------- capabilities

@router.get("/capabilities")
def list_capabilities(active_only: bool = True):
    return repo.list_capabilities(active_only=active_only)


@router.get("/capabilities/{capability_id}")
def get_capability(capability_id: int):
    row = repo.get_capability(capability_id)
    if row is None:
        raise HTTPException(404, "Capability not found")
    return row


@router.post("/capabilities", status_code=201)
def create_capability(payload: CapabilityIn):
    existing = repo.get_capability_by_slug(payload.slug)
    if existing:
        raise HTTPException(409, f"Capability slug already exists: {payload.slug}")
    return repo.create_capability(payload.model_dump())


@router.patch("/capabilities/{capability_id}")
def update_capability(capability_id: int, payload: CapabilityUpdate):
    if repo.get_capability(capability_id) is None:
        raise HTTPException(404, "Capability not found")
    updated = repo.update_capability(capability_id, payload.model_dump(exclude_unset=True))
    return updated


@router.delete("/capabilities/{capability_id}", status_code=204)
def delete_capability(capability_id: int):
    if not repo.delete_capability(capability_id):
        raise HTTPException(404, "Capability not found")


# ---------------------------------------------------------------- evidence

@router.get("/evidence")
def list_evidence(verified_only: bool = False):
    return repo.list_evidence(verified_only=verified_only)


@router.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: int):
    row = repo.get_evidence(evidence_id)
    if row is None:
        raise HTTPException(404, "Evidence not found")
    return row


@router.post("/evidence", status_code=201)
def create_evidence(payload: EvidenceIn):
    return repo.create_evidence(payload.model_dump())


@router.patch("/evidence/{evidence_id}")
def update_evidence(evidence_id: int, payload: EvidenceUpdate):
    if repo.get_evidence(evidence_id) is None:
        raise HTTPException(404, "Evidence not found")
    return repo.update_evidence(evidence_id, payload.model_dump(exclude_unset=True))


@router.delete("/evidence/{evidence_id}", status_code=204)
def delete_evidence(evidence_id: int):
    if not repo.delete_evidence(evidence_id):
        raise HTTPException(404, "Evidence not found")


# ---------------------------------------------------------------- solutions

@router.get("/solutions")
def list_solutions(active_only: bool = True):
    return repo.list_solutions(active_only=active_only)


@router.get("/solutions/{solution_id}")
def get_solution(solution_id: int):
    row = repo.get_solution(solution_id)
    if row is None:
        raise HTTPException(404, "Solution not found")
    return row


@router.post("/solutions", status_code=201)
def create_solution(payload: SolutionIn):
    existing = repo.get_solution_by_slug(payload.slug)
    if existing:
        raise HTTPException(409, f"Solution slug already exists: {payload.slug}")
    return repo.create_solution(payload.model_dump())


@router.patch("/solutions/{solution_id}")
def update_solution(solution_id: int, payload: SolutionUpdate):
    if repo.get_solution(solution_id) is None:
        raise HTTPException(404, "Solution not found")
    return repo.update_solution(solution_id, payload.model_dump(exclude_unset=True))


@router.delete("/solutions/{solution_id}", status_code=204)
def delete_solution(solution_id: int):
    if not repo.delete_solution(solution_id):
        raise HTTPException(404, "Solution not found")


# ---------------------------------------------------------------- problem patterns

@router.get("/patterns")
def list_problem_patterns(active_only: bool = True):
    return repo.list_problem_patterns(active_only=active_only)


@router.get("/patterns/{pattern_id}")
def get_problem_pattern(pattern_id: int):
    row = repo.get_problem_pattern(pattern_id)
    if row is None:
        raise HTTPException(404, "Problem pattern not found")
    return row


@router.post("/patterns", status_code=201)
def create_problem_pattern(payload: ProblemPatternIn):
    created = repo.create_problem_pattern(payload.model_dump())
    if created is None:
        raise HTTPException(409, f"Solution slug not found: {payload.solution_slug}")
    return created


@router.patch("/patterns/{pattern_id}")
def update_problem_pattern(pattern_id: int, payload: ProblemPatternUpdate):
    row = repo.get_problem_pattern(pattern_id)
    if row is None:
        raise HTTPException(404, "Problem pattern not found")
    updated = repo.update_problem_pattern(pattern_id, payload.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(409, "Solution slug not found")
    return updated


@router.delete("/patterns/{pattern_id}", status_code=204)
def delete_problem_pattern(pattern_id: int):
    if not repo.delete_problem_pattern(pattern_id):
        raise HTTPException(404, "Problem pattern not found")


# ---------------------------------------------------------------- matching

@router.get("/match")
def match_business_problem(text: str, top_k: int = 5, min_score: int = 1,
                           include_score: bool = False,
                           size_text: str = "", urgency_text: str = ""):
    if not text.strip():
        raise HTTPException(400, "text is required")
    from service_catalog.matching import match_business_problem as run_match
    from service_catalog.scoring import score_lead
    results = run_match(text, top_k=top_k, min_score=min_score)
    if include_score:
        for item in results:
            item["score"] = score_lead(
                description=text,
                match_score=item["match_score"],
                solution=item["solution"],
                size_text=size_text or text,
                urgency_text=urgency_text or text,
            )
    return results


# ---------------------------------------------------------------- lead matching

@router.get("/leads/{lead_id}/match")
def match_lead(lead_id: str, top_k: int = 5, min_score: int = 1, persist: bool = True):
    from service_catalog.leadmatcher import for_lead
    results = for_lead(lead_id, top_k=top_k, min_score=min_score, persist=persist)
    if results is None:
        raise HTTPException(404, f"Lead not found: {lead_id}")
    return results


@router.get("/leads/{lead_id}/matches")
def get_lead_matches(lead_id: str):
    from service_catalog.leadmatcher import get_stored_matches
    return get_stored_matches(lead_id)