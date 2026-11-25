"""End-to-end test for the user API (ats_engine/server/user_api.py).

Runs the user router on a real uvicorn server and calls it over HTTP. The data
goes to a real MongoDB in a separate test database (TEST_DB), which is dropped
before and after the test. Skipped when MongoDB is not reachable.
"""

import socket
import threading
import time

import httpx
import pytest

pymongo = pytest.importorskip("pymongo")
uvicorn = pytest.importorskip("uvicorn")

from fastapi import FastAPI

import ats_engine.db as ats_db
from ats_engine.constants import DEF_DB_COL_USER
from ats_engine.server.user_api import routerUser

TEST_DB = "ATSDB_TEST"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def test_db():
    """Point the user API at a throwaway MongoDB database."""
    db = ats_db.Db(db=TEST_DB)
    try:
        db.client.server_info()
    except Exception as err:
        pytest.skip(f"MongoDB not reachable: {err}")

    db.client.drop_database(TEST_DB)
    original = ats_db.database
    ats_db.database = db  # user_api reads ats_engine.db.database on every call
    yield db
    ats_db.database = original
    db.client.drop_database(TEST_DB)
    db.client.close()


@pytest.fixture(scope="module")
def client(test_db):
    """Start a uvicorn server with the user router and return an HTTP client for it."""
    app = FastAPI()
    app.include_router(routerUser)

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            pytest.fail("uvicorn did not start within 10 seconds")
        time.sleep(0.05)

    # trust_env=False: ignore HTTP(S)_PROXY so requests go straight to the local server
    base_url = f"http://127.0.0.1:{port}"
    with httpx.Client(base_url=base_url, timeout=5, trust_env=False) as http:
        yield http

    server.should_exit = True
    thread.join(timeout=10)


def test_user_crud_flow(client, test_db):
    # create (email is lowercased and trimmed)
    res = client.post(
        "/users", json={"email": " Alice@Example.com ", "role": "operator"}
    )
    assert res.status_code == 201
    alice = res.json()
    assert alice["email"] == "alice@example.com"
    assert alice["role"] == "operator"
    assert alice["name"] is None
    assert "_id" not in alice and "created_at" in alice and "updated_at" in alice

    # the record really is in MongoDB
    stored = test_db.find_one(DEF_DB_COL_USER, {"email": "alice@example.com"})
    assert stored is not None and stored["role"] == "operator"

    # duplicate email (any case) is rejected
    assert client.post("/users", json={"email": "ALICE@example.com"}).status_code == 409

    # invalid email and missing email are rejected
    assert client.post("/users", json={"email": "not-an-email"}).status_code == 422
    assert client.post("/users", json={"name": "No Email"}).status_code == 422

    assert client.post("/users", json={"email": "bob@example.com"}).status_code == 201

    # list, with paging
    res = client.get("/users")
    assert res.status_code == 200
    assert sorted(u["email"] for u in res.json()) == [
        "alice@example.com",
        "bob@example.com",
    ]
    assert len(client.get("/users", params={"limit": 1}).json()) == 1
    assert len(client.get("/users", params={"skip": 2}).json()) == 0

    # get one (lookup is case-insensitive)
    res = client.get("/users/Alice@Example.com")
    assert res.status_code == 200
    assert res.json()["role"] == "operator"
    assert client.get("/users/nobody@example.com").status_code == 404

    # update only the fields sent
    res = client.put("/users/alice@example.com", json={"name": "Alice"})
    assert res.status_code == 200
    assert res.json()["name"] == "Alice"
    assert res.json()["role"] == "operator"
    assert res.json()["updated_at"] >= alice["updated_at"]

    assert client.put("/users/alice@example.com", json={}).status_code == 400
    assert (
        client.put("/users/nobody@example.com", json={"name": "x"}).status_code == 404
    )

    # changing the email to one that is taken is rejected
    res = client.put("/users/alice@example.com", json={"email": "bob@example.com"})
    assert res.status_code == 409

    # change the email: the old one is gone, the new one works
    res = client.put(
        "/users/alice@example.com", json={"email": "alice.new@example.com"}
    )
    assert res.status_code == 200
    assert res.json()["email"] == "alice.new@example.com"
    assert client.get("/users/alice@example.com").status_code == 404
    assert client.get("/users/alice.new@example.com").json()["name"] == "Alice"

    # delete
    res = client.delete("/users/alice.new@example.com")
    assert res.status_code == 200
    assert res.json() == {"status": "OK", "email": "alice.new@example.com"}
    assert client.get("/users/alice.new@example.com").status_code == 404
    assert client.delete("/users/alice.new@example.com").status_code == 404
    assert test_db.find_one(DEF_DB_COL_USER, {"email": "alice.new@example.com"}) is None

    assert [u["email"] for u in client.get("/users").json()] == ["bob@example.com"]
