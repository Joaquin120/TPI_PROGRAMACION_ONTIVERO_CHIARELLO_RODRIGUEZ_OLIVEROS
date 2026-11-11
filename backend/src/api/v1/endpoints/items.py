from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.item import Item
from src.db.session import get_db
from src.schemas.item import (
    ItemCreate,
    ItemListResponse,
    ItemResponse,
    ItemUpdate,
)

router = APIRouter(tags=["items"])


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> Item:
    """Creates a new item and persists it into the database."""
    item = Item(**item_in.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get(
    "/",
    response_model=ItemListResponse,
    status_code=status.HTTP_200_OK,
    summary="List items with pagination and filters",
)
async def list_items(
    skip: int = Query(default=0, ge=0, description="Items to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Max items to return"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> ItemListResponse:
    """Lists items with offset/limit pagination and optional is_active filter."""
    count_query = select(func.count(Item.id))
    items_query = select(Item).offset(skip).limit(limit)

    if is_active is not None:
        count_query = count_query.where(Item.is_active == is_active)
        items_query = items_query.where(Item.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    items_result = await db.execute(items_query)
    items = list(items_result.scalars().all())

    return ItemListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an item by ID",
)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> Item:
    """Retrieves an item by its unique identifier or raises 404."""
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an item completely",
)
async def update_item(
    item_id: int,
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> Item:
    """Performs a full update of an existing item."""
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    for field, value in item_in.model_dump().items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an item partially",
)
async def patch_item(
    item_id: int,
    item_in: ItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> Item:
    """Performs a partial update of an existing item."""
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    for field, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deletes an item by ID or raises 404."""
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    await db.delete(item)
    await db.commit()
