from pydantic import BaseModel, EmailStr, Field


class BookingSchema(BaseModel):
    """Pydantic V2 schema defining the contract for scheduling validations."""

    full_name: str = Field(
        ..., min_length=1, description="Full name of the interviewee"
    )
    email: EmailStr = Field(..., description="Valid contact email address")
    date: str = Field(
        ...,
        min_length=2,
        description="Target slot date (e.g. YYYY-MM-DD or readable string)",
    )
    time: str = Field(
        ...,
        min_length=2,
        description="Target slot time (e.g. HH:MM or readable string)",
    )
