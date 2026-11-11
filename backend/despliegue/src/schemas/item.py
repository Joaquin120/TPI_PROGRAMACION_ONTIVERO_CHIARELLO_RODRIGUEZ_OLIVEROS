from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Base schema for items containing shared domain attributes."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(
        default=None, max_length=255, description="Optional item description"
    )
    price: float = Field(..., ge=0.0, description="Unit price, non-negative")
    stock: int = Field(default=0, ge=0, description="Inventory count, non-negative")


class ItemCreate(ItemBase):
    """Schema for item creation requests."""

    is_active: bool = Field(
        default=True, description="Active status for the new item"
    )


class ItemUpdate(BaseModel):
    """Schema for updating an item with all fields optional."""

    name: str | None = Field(
        default=None, min_length=1, max_length=100, description="Item name"
    )
    description: str | None = Field(
        default=None, max_length=255, description="Optional item description"
    )
    price: float | None = Field(
        default=None, ge=0.0, description="Unit price, non-negative"
    )
    stock: int | None = Field(
        default=None, ge=0, description="Inventory count, non-negative"
    )
    is_active: bool | None = Field(
        default=None, description="Active status"
    )


class ItemResponse(ItemBase):
    """Schema for item responses including system-generated and audit fields."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemListResponse(BaseModel):
    """Schema for paginated item list responses."""

    items: list[ItemResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
