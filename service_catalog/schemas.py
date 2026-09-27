"""Pydantic schemas for the CLIENTFINDER catalog API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CapabilityIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=80)
    description: str = ""
    proficiency: str = "intermediate"
    verification_level: str = "unvalidated"
    evidence_id: Optional[int] = None
    proven_note: Optional[str] = None
    is_active: bool = True


class CapabilityUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    proficiency: Optional[str] = None
    verification_level: Optional[str] = None
    evidence_id: Optional[int] = None
    proven_note: Optional[str] = None
    is_active: Optional[bool] = None


class EvidenceIn(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)
    role: Optional[str] = None
    description: str = ""
    skills_used: List[str] = []
    url: Optional[str] = None
    date_label: Optional[str] = None
    outcome: Optional[str] = None
    provenance: str = "reported"
    verified: bool = False


class EvidenceUpdate(BaseModel):
    project_name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    skills_used: Optional[List[str]] = None
    url: Optional[str] = None
    date_label: Optional[str] = None
    outcome: Optional[str] = None
    provenance: Optional[str] = None
    verified: Optional[bool] = None


class SolutionIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = None
    problem_text: Optional[str] = None
    deliverables: List[str] = []
    capability_slugs: List[str] = []
    evidence_ids: List[int] = []
    typical_effort_label: Optional[str] = None
    is_active: bool = True


class SolutionUpdate(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    problem_text: Optional[str] = None
    deliverables: Optional[List[str]] = None
    capability_slugs: Optional[List[str]] = None
    evidence_ids: Optional[List[int]] = None
    typical_effort_label: Optional[str] = None
    is_active: Optional[bool] = None


class ProblemPatternIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=120)
    label: str = Field(..., min_length=1, max_length=200)
    keywords: List[str] = Field(..., min_length=1)
    description: Optional[str] = None
    solution_slug: str = Field(..., min_length=1, max_length=120)
    urgency_hint: Optional[str] = None
    size_hint: Optional[str] = None
    is_active: bool = True


class ProblemPatternUpdate(BaseModel):
    label: Optional[str] = None
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    solution_slug: Optional[str] = None
    urgency_hint: Optional[str] = None
    size_hint: Optional[str] = None
    is_active: Optional[bool] = None