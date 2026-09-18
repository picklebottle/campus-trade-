from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, get_current_user_optional
from ..utils import save_image

router = APIRouter(prefix="/api/items", tags=["items"])


def _serialize(item: models.Item, wishlisted_ids: set) -> schemas.ItemOut:
    out = schemas.ItemOut.model_validate(item)
    out.is_wishlisted = item.id in wishlisted_ids
    return out


def _wishlisted_ids(db: Session, user: Optional[models.User]) -> set:
    if not user:
        return set()
    rows = db.query(models.WishlistEntry.item_id).filter(models.WishlistEntry.user_id == user.id).all()
    return {r[0] for r in rows}


@router.get("", response_model=schemas.PaginatedItems)
def list_items(
    search: Optional[str] = Query(None, description="Matches title or category"),
    category: Optional[str] = Query(None, description="'all' or omit for every category"),
    sort: str = Query("recent", pattern="^(recent|low|high)$"),
    status: str = Query("active", description="active | sold | draft | all"),
    mine: bool = Query(False, description="Only the current user's own listings"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    q = db.query(models.Item)

    if status != "all":
        q = q.filter(models.Item.status == status)

    if mine:
        if not current_user:
            raise HTTPException(status_code=401, detail="Login required to view your own listings.")
        q = q.filter(models.Item.seller_id == current_user.id)

    if category and category != "all":
        q = q.filter(models.Item.category == category)

    if search:
        like = f"%{search.lower()}%"
        q = q.filter(or_(
            models.Item.title.ilike(like),
            models.Item.category.ilike(like),
            models.Item.description.ilike(like),
        ))

    total = q.count()

    if sort == "low":
        q = q.order_by(models.Item.price.asc())
    elif sort == "high":
        q = q.order_by(models.Item.price.desc())
    else:
        q = q.order_by(models.Item.created_at.desc())

    rows = q.offset(offset).limit(limit).all()
    wishlisted = _wishlisted_ids(db, current_user)
    return schemas.PaginatedItems(total=total, items=[_serialize(i, wishlisted) for i in rows])


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return _serialize(item, _wishlisted_ids(db, current_user))


@router.post("", response_model=schemas.ItemOut, status_code=201)
def create_item(
    payload: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.status not in {s.value for s in models.ItemStatus}:
        raise HTTPException(status_code=422, detail="Invalid status.")
    if payload.condition not in {c.value for c in models.Condition}:
        raise HTTPException(status_code=422, detail="Invalid condition.")

    item = models.Item(
        title=payload.title,
        description=payload.description,
        price=payload.price,
        category=payload.category,
        condition=payload.condition,
        status=payload.status,
        seller_id=current_user.id,
    )
    db.add(item)
    db.flush()  # get item.id before attaching images

    for idx, src in enumerate(payload.image_urls):
        try:
            url = save_image(src)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        db.add(models.ItemImage(item_id=item.id, url=url, position=idx))

    db.commit()
    db.refresh(item)
    return _serialize(item, _wishlisted_ids(db, current_user))


@router.patch("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own listings.")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] == models.ItemStatus.sold.value:
        from datetime import datetime
        item.sold_at = datetime.utcnow()
    for field, value in data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return _serialize(item, _wishlisted_ids(db, current_user))


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings.")
    db.delete(item)
    db.commit()
    return None


@router.get("/meta/categories")
def list_categories():
    return [
        {"id": "books", "name": "Books", "description": "Textbooks, notes & guides"},
        {"id": "electronics", "name": "Electronics", "description": "Tech that keeps up"},
        {"id": "calculators", "name": "Calculators", "description": "For every semester"},
        {"id": "cycles", "name": "Cycles", "description": "Get around campus"},
        {"id": "bags", "name": "Bags", "description": "Carry your day"},
        {"id": "hostel", "name": "Hostel Essentials", "description": "Make it yours"},
    ]
