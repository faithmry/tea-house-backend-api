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
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str


class AuthResponse(BaseModel):
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


class MenuItemOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    name: str
    description: str
    price: float
    category: str
    image_url: str | None = Field(default=None, alias="imageUrl")
    is_available: bool = Field(alias="isAvailable")


class OrderItemIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    menu_item_id: str = Field(alias="menuItemId")
    quantity: int


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    member_id: str = Field(alias="memberId")
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    menu_item_id: str = Field(alias="menuItemId")
    menu_item_name: str = Field(alias="menuItemName")
    quantity: int
    unit_price: float = Field(alias="unitPrice")


class OrderOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    member_id: str = Field(alias="memberId")
    total_amount: float = Field(alias="totalAmount")
    status: str
    created_at: str = Field(alias="createdAt")
    items: list[OrderItemOut] = []


class UpdateOrderStatusRequest(BaseModel):
    status: str
