"""JSON request/response models — equivalent of the Kotlin @Serializable classes.

`alias`/`populate_by_name` keep the JSON keys identical to the Kotlin API
(`memberId`, `pointsEarned`, `profilePictureUrl`) so existing clients (the
Android app) don't have to change.
"""

from pydantic import BaseModel, ConfigDict, Field


class MemberOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    name: str
    email: str
    phone: str
    points: int
    tier: str
    profile_picture_url: str | None = Field(default=None, alias="profilePictureUrl")


class LoginRequest(BaseModel):
    phone: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str


class AuthResponse(BaseModel):
    """Returned by /login and /register: a token plus the member profile."""

    token: str
    member_id: str = Field(serialization_alias="memberId")
    member: MemberOut


class TransactionRequest(BaseModel):
    member_id: str = Field(alias="memberId")
    amount: float


class TransactionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    member_id: str = Field(alias="memberId")
    amount: float
    points_earned: int = Field(alias="pointsEarned")
    date: str
    type: str
