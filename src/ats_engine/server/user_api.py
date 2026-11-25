"""User CRUD API router (stored in the MongoDB 'user' collection).

Enabled by ENGINE_FLAGS["enable_api_user"] (see ats_engine/constants.py).
A user is identified by its email.

Routes (prefix /users):
    POST   /users           create a user
    GET    /users           list users (?skip=0&limit=100)
    GET    /users/{email}   get one user
    PUT    /users/{email}   update a user (only the fields sent are changed)
    DELETE /users/{email}   delete a user
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ats_engine.constants import DEF_DB_COL_USER, DEF_OK

logger = logging.getLogger("[framework]")

routerUser = APIRouter(prefix="/users", tags=["users"])

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+$"


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(pattern=EMAIL_PATTERN)
    name: str | None = None
    role: str | None = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str | None = Field(default=None, pattern=EMAIL_PATTERN)
    name: str | None = None
    role: str | None = None


def _db():
    # imported here: ats_engine.db creates the MongoDB client on import
    from ats_engine.db import database

    return database


def _normalize(email: str) -> str:
    return email.strip().lower()


def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


def _db_call(func, *args, **kwargs):
    """Run a database call and turn connection errors into HTTP 503."""
    try:
        return func(*args, **kwargs)
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"user api database error: {err}")
        raise HTTPException(status_code=503, detail=f"database error: {err}")


def _find(email: str):
    return _db_call(_db().find_one, DEF_DB_COL_USER, {"email": _normalize(email)})


@routerUser.post("", status_code=201)
def user_create(user: UserCreate):
    email = _normalize(user.email)
    if _find(email) is not None:
        raise HTTPException(status_code=409, detail=f"user '{email}' already exists")

    now = datetime.now()
    doc = {**user.model_dump(), "email": email, "created_at": now, "updated_at": now}
    _db_call(_db().insert_one, DEF_DB_COL_USER, doc)
    logger.info(f"user created via API: {email}")
    return _serialize(doc)


@routerUser.get("")
def user_list(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    docs = _db_call(_db().find_many, DEF_DB_COL_USER, {}, skip=skip, limit=limit)
    return [_serialize(doc) for doc in docs]


@routerUser.get("/{email}")
def user_get(email: str):
    doc = _find(email)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"user '{email}' not found")
    return _serialize(doc)


@routerUser.put("/{email}")
def user_update(email: str, user: UserUpdate):
    email = _normalize(email)
    changes = user.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="no fields to update")

    if "email" in changes:
        changes["email"] = _normalize(changes["email"])
        if changes["email"] != email and _find(changes["email"]) is not None:
            raise HTTPException(
                status_code=409, detail=f"user '{changes['email']}' already exists"
            )

    changes["updated_at"] = datetime.now()
    res = _db_call(_db().update_one, DEF_DB_COL_USER, {"email": email}, changes)
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"user '{email}' not found")

    logger.info(f"user updated via API: {email}")
    doc = _find(changes.get("email", email))
    if doc is None:  # deleted between the update and the read
        raise HTTPException(status_code=404, detail=f"user '{email}' not found")
    return _serialize(doc)


@routerUser.delete("/{email}")
def user_delete(email: str):
    email = _normalize(email)
    res = _db_call(_db().delete_one, DEF_DB_COL_USER, {"email": email})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"user '{email}' not found")

    logger.info(f"user deleted via API: {email}")
    return {"status": DEF_OK, "email": email}
