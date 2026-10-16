import datetime
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from filelock import FileLock

from config.local_query import matches_document


logger = logging.getLogger("SupportNova.Database")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_store")
os.makedirs(DATA_DIR, exist_ok=True)


def save_json_atomic(file_path: str, data: list):
    lock_path = file_path + ".lock"
    dir_name = os.path.dirname(file_path)
    os.makedirs(dir_name, exist_ok=True)
    try:
        try:
            with FileLock(lock_path, timeout=2):
                with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                    json.dump(data, tf, indent=2, default=str)
                    temp_name = tf.name
                os.replace(temp_name, file_path)
        except Exception:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, default=str)
    except Exception as error:
        logger.error(f"Save error for {file_path}: {error}")


class LocalJSONCollection:
    def __init__(self, name: str):
        self.name = name
        self.filepath = os.path.join(DATA_DIR, f"{name}.json")
        self._data: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            self._data = []
            return
        lock_path = self.filepath + ".lock"
        try:
            try:
                with FileLock(lock_path, timeout=2):
                    with open(self.filepath, "r", encoding="utf-8") as file:
                        self._data = json.load(file)
            except Exception:
                with open(self.filepath, "r", encoding="utf-8") as file:
                    self._data = json.load(file)
        except Exception as error:
            logger.error(f"Error loading {self.filepath}: {error}")
            self._data = []

    def _save(self):
        save_json_atomic(self.filepath, self._data)

    def insert_one(self, doc: Dict[str, Any]):
        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = f"{self.name}_{len(self._data) + 1}_{int(datetime.datetime.now().timestamp())}"
        self._data.append(doc_copy)
        self._save()
        return type("InsertResult", (), {"inserted_id": doc_copy["_id"]})()

    def insert_many(self, docs: List[Dict[str, Any]]):
        ids = []
        for doc in docs:
            doc_copy = dict(doc)
            if "_id" not in doc_copy:
                doc_copy["_id"] = f"{self.name}_{len(self._data) + 1}_{int(datetime.datetime.now().timestamp())}"
            self._data.append(doc_copy)
            ids.append(doc_copy["_id"])
        self._save()
        return type("InsertManyResult", (), {"inserted_ids": ids})()

    @staticmethod
    def _matches(item: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        return matches_document(item, filter_dict)

    def find(self, filter_dict: Optional[Dict[str, Any]] = None, sort: Optional[List] = None, limit: int = 0):
        results = [item for item in self._data if self._matches(item, filter_dict or {})]
        if sort:
            field, direction = sort[0]
            results.sort(key=lambda item: str(item.get(field, "")), reverse=direction < 0)
        return results[:limit] if limit > 0 else results

    def find_one(self, filter_dict: Dict[str, Any]):
        results = self.find(filter_dict, limit=1)
        return results[0] if results else None

    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        for item in self._data:
            if self._matches(item, filter_dict):
                if "$set" in update_dict:
                    item.update(update_dict["$set"])
                if "$push" in update_dict:
                    for key, value in update_dict["$push"].items():
                        item.setdefault(key, [])
                        if isinstance(item[key], list):
                            item[key].append(value)
                self._save()
                return type("UpdateResult", (), {"modified_count": 1})()
        return type("UpdateResult", (), {"modified_count": 0})()

    def delete_one(self, filter_dict: Dict[str, Any]):
        for index, item in enumerate(self._data):
            if self._matches(item, filter_dict):
                self._data.pop(index)
                self._save()
                return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()

    def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None):
        return len(self.find(filter_dict))
