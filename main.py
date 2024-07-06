from fastapi import FastAPI, Depends, HTTPException, Query


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


from typing import List, Optional

import schemas
from config import settings
from helper import get_password_hash
from models import Item, ItemHistory, User

Base = declarative_base()

engine = create_engine(settings.DATABASE_URI)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


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
    return db.query(Item).get(id)


@app.get("/")
def read_root():
    return {"Hello": "Azure"}


@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, q: Optional[str] = None, db: Session = Depends(get_db)):
    # TODO: Figure out what to do with  Query parameter passed
    if q:
        return {"item_id": item_id, "q": q}
    item = get_item_by_id(db, item_id)
    return item


@app.post("/users/", response_model=schemas.User)
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )
    return create_user(db=db, user=user)


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    return create_user_item(db=db, item=item, user_id=user_id)


@app.post("/reassign_item/{item_id}/", response_model=schemas.Item)
def assign_item(item_id: int, new_owner: schemas.UserId, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item does not exist")
    user = db.query(User).get(new_owner.id)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    item.owner_id = new_owner.id
    db.add(item)
    db.commit()
    add_history(db, item, new_owner.id)
    return item


@app.patch("/items/{item_id}/", response_model=schemas.Item)
def modify_item_status(
    item_id: int, item_status: schemas.ItemStatus, db: Session = Depends(get_db)
):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item does not exist")
    item.status = item_status.status.value
    db.add(item)
    db.commit()
    return item


@app.get("/items/", response_model=list[schemas.Item])
def list_items(
    status: schemas.ItemStatusChoices = Query(schemas.ItemStatusChoices.NEW),
    db: Session = Depends(get_db),
):
    items = db.query(Item).filter(Item.status == status.value).all()
    return items
