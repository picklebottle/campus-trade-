from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me/dashboard", response_model=schemas.DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    q = db.query(models.Item).filter(models.Item.seller_id == current_user.id)
    active = q.filter(models.Item.status == models.ItemStatus.active).count()
    sold = q.filter(models.Item.status == models.ItemStatus.sold).count()
    drafts = q.filter(models.Item.status == models.ItemStatus.draft).count()

    # bump the profile-view counter a little each time someone checks the dashboard/profile
    current_user.profile_views += 1
    db.commit()

    return schemas.DashboardStats(
        active_listings=active,
        sold_items=sold,
        drafts=drafts,
        profile_views=current_user.profile_views,
        rating=current_user.rating,
    )


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_public_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found.")
    return user
