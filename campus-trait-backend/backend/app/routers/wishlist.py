from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("", response_model=schemas.WishlistOut)
def get_wishlist(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    entries = (
        db.query(models.WishlistEntry)
        .filter(models.WishlistEntry.user_id == current_user.id)
        .order_by(models.WishlistEntry.created_at.desc())
        .all()
    )
    ids = {e.item_id for e in entries}
    out_items = []
    for e in entries:
        out = schemas.ItemOut.model_validate(e.item)
        out.is_wishlisted = True
        out_items.append(out)
    return schemas.WishlistOut(items=out_items)


@router.post("/{item_id}", status_code=201)
def add_to_wishlist(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    existing = (
        db.query(models.WishlistEntry)
        .filter(models.WishlistEntry.user_id == current_user.id, models.WishlistEntry.item_id == item_id)
        .first()
    )
    if existing:
        return {"wishlisted": True}

    db.add(models.WishlistEntry(user_id=current_user.id, item_id=item_id))
    db.commit()
    return {"wishlisted": True}


@router.delete("/{item_id}", status_code=204)
def remove_from_wishlist(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    entry = (
        db.query(models.WishlistEntry)
        .filter(models.WishlistEntry.user_id == current_user.id, models.WishlistEntry.item_id == item_id)
        .first()
    )
    if entry:
        db.delete(entry)
        db.commit()
    return None


@router.post("/{item_id}/toggle")
def toggle_wishlist(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    entry = (
        db.query(models.WishlistEntry)
        .filter(models.WishlistEntry.user_id == current_user.id, models.WishlistEntry.item_id == item_id)
        .first()
    )
    if entry:
        db.delete(entry)
        db.commit()
        return {"wishlisted": False}

    db.add(models.WishlistEntry(user_id=current_user.id, item_id=item_id))
    db.commit()
    return {"wishlisted": True}
