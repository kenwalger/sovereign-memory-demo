"""Pydantic schemas for fail-fast dataset validation."""

from pydantic import BaseModel, Field


class AccessionRecordSchema(BaseModel):
    """Schema for a single accession registry row."""

    accession_number: str = Field(min_length=1)
    title: str = Field(min_length=1)
    date_acquired: str = Field(min_length=1)
    source: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class PhotographRecordSchema(BaseModel):
    """Schema for a single photograph catalog row."""

    photo_id: str = Field(min_length=1)
    caption: str = Field(min_length=1)
    estimated_year: int = Field(ge=1, le=9999)
    subjects: list[str] = Field(min_length=1)
