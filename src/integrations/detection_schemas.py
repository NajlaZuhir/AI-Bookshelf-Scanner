"""Structured response models for bookshelf image detection."""

from pydantic import BaseModel, ConfigDict, Field


class Book(BaseModel):
    model_config = ConfigDict(extra="forbid")

    book_number: int = Field(description="The book's position in the image, starting from 1.")
    title: str = Field(description="The readable title visible in the image.")
    author: str | None = Field(
        description="The author visible in the image, or null if unreadable."
    )


class BookDetectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    books: list[Book]
