from config.database import LocalJSONCollection


def test_local_collection_supports_common_operators_without_persisting(tmp_path, monkeypatch):
    collection = LocalJSONCollection("query-test")
    collection.filepath = str(tmp_path / "records.json")
    monkeypatch.setattr(collection, "_save", lambda: None)
    collection._data = [
        {"_id": "one", "role": "agent", "status": "open", "score": 3},
        {"_id": "two", "role": "admin", "status": "closed", "score": 7},
        {"_id": "three", "role": "agent", "score": 9},
    ]

    assert [row["_id"] for row in collection.find({"role": {"$in": ["agent"]}})] == ["one", "three"]
    assert [row["_id"] for row in collection.find({"status": {"$exists": False}})] == ["three"]
    assert collection.find_one({"role": "agent", "$or": [{"_id": "two"}, {"score": {"$ne": 3}}]})["_id"] == "three"
    collection.update_one({"score": {"$in": [7]}}, {"$set": {"status": "review"}})
    assert collection.find_one({"_id": "two"})["status"] == "review"
