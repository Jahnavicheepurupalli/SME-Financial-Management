import json
import socket

import pytest

from backend.database.db import MockMongoCollection, MockMongoDB, is_mongo_port_open


def test_mock_mongo_crud_and_corrupt_file(tmp_path):
    path = tmp_path / "mongo.json"
    collection = MockMongoCollection(str(path), "items")
    inserted = collection.insert_one({"name": "one", "kind": "a"})
    assert inserted.inserted_id
    assert collection.find_one({"name": "one"})["name"] == "one"
    assert collection.find_one({"name": "missing"}) is None
    assert len(collection.find()) == 1
    assert collection.find({"kind": "a"})[0]["name"] == "one"
    assert collection.find({"kind": "b"}) == []

    original_id = collection.find_one({"name": "one"})["_id"]
    result = collection.replace_one({"name": "one"}, {"name": "updated"}, upsert=False)
    assert result.matched_count == 1
    assert collection.find_one({"name": "updated"})["_id"] == original_id
    assert collection.replace_one({"name": "none"}, {"name": "new"}, upsert=False).matched_count == 0
    collection.replace_one({"name": "new"}, {"name": "new"}, upsert=True)
    assert collection.find_one({"name": "new"})
    assert collection.delete_one({"name": "new"}).deleted_count == 1
    collection.insert_one({"group": "x"})
    collection.insert_one({"group": "x"})
    assert collection.delete_many({"group": "x"}).deleted_count == 2

    path.write_text("{not-json")
    with pytest.raises(json.JSONDecodeError):
        collection._read_data()


def test_mock_db_binds_collections_to_same_file(tmp_path):
    db = MockMongoDB(str(tmp_path / "db.json"))
    first = db["first"]
    second = db["second"]
    assert first.db_path == second.db_path == db.db_path
    first.insert_one({"value": 1})
    assert second.find() == []


def test_mongo_port_check_closed_and_open():
    assert is_mongo_port_open("mongodb://127.0.0.1:1") is False
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    try:
        assert is_mongo_port_open(f"mongodb://127.0.0.1:{listener.getsockname()[1]}") is True
    finally:
        listener.close()
