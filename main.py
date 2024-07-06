from fastapi import FastAPI, Depends, HTTPException, Query

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, Session


from typing import Optional

import schemas
from config import settings
from crud import (
    get_item_by_id,
    get_user_by_email,
    create_user,
    create_user_item,
    add_history,
    add_status_history,
)
from exception import CustomBaseException


from models import Item, User, Base

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


@app.get("/")
def read_root():
    return {"Hello": "Azure"}


@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, q: Optional[str] = None, db: Session = Depends(get_db)):
    # TODO: Figure out what to do with  Query parameter passed
    if q:
        return {"item_id": item_id, "q": q}
    try:
        item = get_item_by_id(db, item_id)
    except CustomBaseException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
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
    try:
        item = get_item_by_id(db, item_id)
    except CustomBaseException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
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
    try:
        item = get_item_by_id(db, item_id)
    except CustomBaseException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    item.status = item_status.status.value
    db.add(item)
    db.commit()
    # Add history entry
    add_status_history(db, item)
    return item


@app.get("/items/", response_model=list[schemas.Item])
def list_items(
    status: schemas.ItemStatusChoices = Query(schemas.ItemStatusChoices.NEW),
    db: Session = Depends(get_db),
):
    items = db.query(Item).filter(Item.status == status.value).all()
    return items
