"""Pydantic schemas for fail-fast dataset validation."""

from pydantic import BaseModel, Field


class AccessionRecordSchema(BaseModel):
    """Schema for a single accession registry row.

    :ivar str accession_number: Unique accession identifier.
    :ivar str title: Descriptive title of the accessioned item.
    :ivar str date_acquired: Acquisition date string from the source dataset.
    :ivar str source: Provenance source of the accession.
    :ivar float confidence: Confidence score in the range ``[0.0, 1.0]``.
    """

    accession_number: str = Field(min_length=1)
    title: str = Field(min_length=1)
    date_acquired: str = Field(min_length=1)
    source: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class PhotographRecordSchema(BaseModel):
    """Schema for a single photograph catalog row.

    :ivar str photo_id: Unique photograph identifier.
    :ivar str caption: Descriptive caption for the photograph.
    :ivar int estimated_year: Estimated year of capture (1–9999).
    :ivar list[str] subjects: Non-empty list of subject labels.
    """

    photo_id: str = Field(min_length=1)
    caption: str = Field(min_length=1)
    estimated_year: int = Field(ge=1, le=9999)
    subjects: list[str] = Field(min_length=1)
