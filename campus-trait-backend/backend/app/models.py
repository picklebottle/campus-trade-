"""
SQLAlchemy ORM models for Campus Trait.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text,
    Enum, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class ItemStatus(str, enum.Enum):
    active = "active"
    sold = "sold"
    draft = "draft"


class Condition(str, enum.Enum):
    like_new = "Like new"
    good = "Good condition"
    fair = "Fair condition"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    college = Column(String(180), default="")
    department = Column(String(120), default="")
    year = Column(String(40), default="")
    rating = Column(Float, default=5.0)
    profile_views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("Item", back_populates="seller", cascade="all, delete-orphan")
    wishlist_entries = relationship("WishlistEntry", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")

    @property
    def initials(self) -> str:
        parts = self.name.split()
        return "".join(p[0] for p in parts[:2]).upper() if parts else "?"


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False, default=0)
    category = Column(String(60), nullable=False, index=True)
    condition = Column(Enum(Condition), default=Condition.good)
    status = Column(Enum(ItemStatus), default=ItemStatus.active, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sold_at = Column(DateTime, nullable=True)

    seller = relationship("User", back_populates="items")
    images = relationship("ItemImage", back_populates="item", cascade="all, delete-orphan", order_by="ItemImage.position")
    wishlisted_by = relationship("WishlistEntry", back_populates="item", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="item")

    @property
    def cover_image(self):
        return self.images[0].url if self.images else None


class ItemImage(Base):
    __tablename__ = "item_images"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    url = Column(String(500), nullable=False)
    position = Column(Integer, default=0)

    item = relationship("Item", back_populates="images")


class WishlistEntry(Base):
    __tablename__ = "wishlist_entries"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_user_item_wishlist"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wishlist_entries")
    item = relationship("Item", back_populates="wishlisted_by")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="conversations")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
