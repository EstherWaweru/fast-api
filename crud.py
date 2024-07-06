from sqlalchemy.orm import Session

import schemas
from exception import CustomBaseException
from helper import get_password_hash
from models import User, Item, ItemHistory


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return db_user


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    return db_item


def add_history(db: Session, item, new_owner_id):
    history_entry = ItemHistory(
        item_id=item.id, old_assignee=item.owner_id, new_assignee=new_owner_id
    )
    db.add(history_entry)
    db.commit()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_item_by_id(db: Session, id: int):
    item = db.query(Item).get(id)
    if not item:
        raise CustomBaseException("Item does not exist")
    return item


def add_status_history(db: Session, item):
    history_entry = ItemHistory(item_id=item.id, status=item.status)
    db.add(history_entry)
    db.commit()
