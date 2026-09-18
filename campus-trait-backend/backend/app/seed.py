"""
Seeds the database with demo data that mirrors the Campus Trait frontend
mockups, so the API is immediately useful to explore.

Runs automatically on startup (see main.py) if the users table is empty.
Demo login for every seeded user is password: "password123"
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from . import models
from .security import hash_password

DEMO_PASSWORD = "password123"

DEMO_ITEMS = [
    dict(title="Casio Scientific Calculator", price=700, category="calculators",
         condition=models.Condition.good, seller_email="aarav@campustrait.edu",
         img="https://images.unsplash.com/photo-1587145717905-2624ba1ee49c?w=700&q=80&auto=format&fit=crop",
         desc="Barely used, all functions work perfectly. Great for engineering coursework."),
    dict(title="MacBook Air M1", price=48000, category="electronics",
         condition=models.Condition.like_new, seller_email="ananya@campustrait.edu",
         img="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=700&q=80&auto=format&fit=crop",
         desc="Used for one semester, 256GB, Space Grey, battery health 96%."),
    dict(title="Engineering Mathematics Vol. 2", price=350, category="books",
         condition=models.Condition.fair, seller_email="vikram@campustrait.edu",
         img="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=700&q=80&auto=format&fit=crop",
         desc="Some highlighting in early chapters but binding is intact."),
    dict(title="Urban commuter bicycle", price=4500, category="cycles",
         condition=models.Condition.good, seller_email="ishita@campustrait.edu",
         img="https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=700&q=80&auto=format&fit=crop",
         desc="Single-speed, recently serviced with new brake pads."),
    dict(title="IKEA study lamp", price=900, category="hostel",
         condition=models.Condition.like_new, seller_email="dev@campustrait.edu",
         img="https://images.unsplash.com/photo-1543198126-06c8fe6c8c85?w=700&q=80&auto=format&fit=crop",
         desc="Adjustable arm, warm and cool light settings."),
    dict(title="Canvas laptop backpack", price=1200, category="bags",
         condition=models.Condition.good, seller_email="meera@campustrait.edu",
         img="https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=700&q=80&auto=format&fit=crop",
         desc="Fits up to 15-inch laptops, padded compartment."),
]

DEMO_USERS = [
    dict(name="Aarav Sharma", email="aarav@campustrait.edu", college="Delhi University", department="Computer Science", year="3rd Year"),
    dict(name="Ananya Rao", email="ananya@campustrait.edu", college="Delhi University", department="Economics", year="4th Year"),
    dict(name="Vikram Kapoor", email="vikram@campustrait.edu", college="Delhi University", department="Mechanical Eng.", year="3rd Year"),
    dict(name="Ishita Verma", email="ishita@campustrait.edu", college="Delhi University", department="Design", year="2nd Year"),
    dict(name="Dev Malhotra", email="dev@campustrait.edu", college="Delhi University", department="Physics", year="1st Year"),
    dict(name="Meera Nair", email="meera@campustrait.edu", college="Delhi University", department="Literature", year="3rd Year"),
    dict(name="Nisha Sharma", email="nisha@campustrait.edu", college="Delhi University", department="Chemistry", year="2nd Year"),
]


def run_seed(db: Session):
    if db.query(models.User).count() > 0:
        return  # already seeded

    users_by_email = {}
    for u in DEMO_USERS:
        user = models.User(
            name=u["name"], email=u["email"], hashed_password=hash_password(DEMO_PASSWORD),
            college=u["college"], department=u["department"], year=u["year"],
            rating=4.9, profile_views=2400,
        )
        db.add(user)
        db.flush()
        users_by_email[u["email"]] = user

    for i, it in enumerate(DEMO_ITEMS):
        item = models.Item(
            title=it["title"], description=it["desc"], price=it["price"], category=it["category"],
            condition=it["condition"], status=models.ItemStatus.active,
            seller_id=users_by_email[it["seller_email"]].id,
            created_at=datetime.utcnow() - timedelta(hours=i * 5),
        )
        db.add(item)
        db.flush()
        db.add(models.ItemImage(item_id=item.id, url=it["img"], position=0))

    db.commit()

    # a demo conversation: Nisha asking Aarav about the calculator
    aarav = users_by_email["aarav@campustrait.edu"]
    nisha = users_by_email["nisha@campustrait.edu"]
    calculator = db.query(models.Item).filter(models.Item.title == "Casio Scientific Calculator").first()

    convo = models.Conversation(item_id=calculator.id, buyer_id=nisha.id, seller_id=aarav.id)
    db.add(convo)
    db.flush()
    db.add(models.Message(conversation_id=convo.id, sender_id=nisha.id, text="Hey, is this calculator still available?", is_read=True))
    db.add(models.Message(conversation_id=convo.id, sender_id=aarav.id, text="Yes, it's available! I'm near the library after 3pm.", is_read=True))
    db.add(models.Message(conversation_id=convo.id, sender_id=nisha.id, text="Perfect, see you then!", is_read=False))
    db.commit()
