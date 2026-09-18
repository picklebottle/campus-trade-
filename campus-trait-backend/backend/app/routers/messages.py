from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["messages"])


def _unread_count(conv: models.Conversation, user_id: int) -> int:
    return sum(1 for m in conv.messages if not m.is_read and m.sender_id != user_id)


@router.get("", response_model=list[schemas.ConversationOut])
def list_conversations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    convos = (
        db.query(models.Conversation)
        .filter(or_(models.Conversation.buyer_id == current_user.id, models.Conversation.seller_id == current_user.id))
        .order_by(models.Conversation.id.desc())
        .all()
    )
    result = []
    for c in convos:
        out = schemas.ConversationOut.model_validate(c)
        out.unread_count = _unread_count(c, current_user.id)
        result.append(out)
    return result


@router.post("", response_model=schemas.ConversationOut, status_code=201)
def start_conversation(
    payload: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Item).filter(models.Item.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't start a conversation about your own listing.")

    existing = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.item_id == item.id,
            models.Conversation.buyer_id == current_user.id,
            models.Conversation.seller_id == item.seller_id,
        )
        .first()
    )
    convo = existing or models.Conversation(item_id=item.id, buyer_id=current_user.id, seller_id=item.seller_id)
    if not existing:
        db.add(convo)
        db.flush()

    if payload.opening_message:
        db.add(models.Message(conversation_id=convo.id, sender_id=current_user.id, text=payload.opening_message))

    db.commit()
    db.refresh(convo)
    out = schemas.ConversationOut.model_validate(convo)
    out.unread_count = _unread_count(convo, current_user.id)
    return out


def _get_owned_conversation(db: Session, conversation_id: int, user_id: int) -> models.Conversation:
    convo = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if user_id not in (convo.buyer_id, convo.seller_id):
        raise HTTPException(status_code=403, detail="You don't have access to this conversation.")
    return convo


@router.get("/{conversation_id}", response_model=schemas.ConversationOut)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    convo = _get_owned_conversation(db, conversation_id, current_user.id)
    # mark incoming messages as read
    changed = False
    for m in convo.messages:
        if m.sender_id != current_user.id and not m.is_read:
            m.is_read = True
            changed = True
    if changed:
        db.commit()
        db.refresh(convo)
    out = schemas.ConversationOut.model_validate(convo)
    out.unread_count = 0
    return out


@router.post("/{conversation_id}/messages", response_model=schemas.MessageOut, status_code=201)
def send_message(
    conversation_id: int,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    convo = _get_owned_conversation(db, conversation_id, current_user.id)
    message = models.Message(conversation_id=convo.id, sender_id=current_user.id, text=payload.text)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
