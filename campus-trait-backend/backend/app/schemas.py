"""
Pydantic schemas — request bodies and API response shapes.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- auth / users ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    college: str = ""
    department: str = ""
    year: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    college: str
    department: str
    year: str
    rating: float
    profile_views: int
    initials: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- items ----------
class ItemImageOut(BaseModel):
    id: int
    url: str
    position: int

    class Config:
        from_attributes = True


class ItemCreate(BaseModel):
    title: str
    description: str = ""
    price: float
    category: str
    condition: str = "Good condition"
    status: str = "active"
    image_urls: List[str] = []  # base64 data-URIs or hosted URLs


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    status: Optional[str] = None


class SellerOut(BaseModel):
    id: int
    name: str
    initials: str
    year: str

    class Config:
        from_attributes = True


class ItemOut(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str
    condition: str
    status: str
    created_at: datetime
    sold_at: Optional[datetime]
    seller: SellerOut
    images: List[ItemImageOut]
    is_wishlisted: bool = False

    class Config:
        from_attributes = True


class PaginatedItems(BaseModel):
    total: int
    items: List[ItemOut]


# ---------- wishlist ----------
class WishlistOut(BaseModel):
    items: List[ItemOut]


# ---------- messaging ----------
class MessageCreate(BaseModel):
    text: str = Field(min_length=1)


class MessageOut(BaseModel):
    id: int
    text: str
    sender_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    item_id: int
    opening_message: Optional[str] = None


class ConversationOut(BaseModel):
    id: int
    item: Optional[ItemOut]
    buyer: SellerOut
    seller: SellerOut
    messages: List[MessageOut]
    unread_count: int = 0

    class Config:
        from_attributes = True


# ---------- dashboard ----------
class DashboardStats(BaseModel):
    active_listings: int
    sold_items: int
    drafts: int
    profile_views: int
    rating: float
