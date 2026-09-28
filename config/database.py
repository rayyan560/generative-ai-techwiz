import os
import json
import logging
import datetime
import tempfile
from typing import Dict, Any, List, Optional
from filelock import FileLock
from config.settings import settings

logger = logging.getLogger("SupportNova.Database")

# Memory/File fallback store directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_store")
os.makedirs(DATA_DIR, exist_ok=True)

def save_json_atomic(file_path: str, data: list):
    """Atomic write with fast inter-process file locking to prevent data corruption during concurrent writes."""
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
            # Fallback direct write if filelock times out
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Save error for {file_path}: {e}")

class LocalJSONCollection:
    """High-performance local JSON fallback collection matching pymongo syntax"""
    def __init__(self, name: str):
        self.name = name
        self.filepath = os.path.join(DATA_DIR, f"{name}.json")
        self._data: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            lock_path = self.filepath + ".lock"
            try:
                try:
                    with FileLock(lock_path, timeout=2):
                        with open(self.filepath, "r", encoding="utf-8") as f:
                            self._data = json.load(f)
                except Exception:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading {self.filepath}: {e}")
                self._data = []
        else:
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

    def find(self, filter_dict: Optional[Dict[str, Any]] = None, sort: Optional[List] = None, limit: int = 0):
        results = []
        filter_dict = filter_dict or {}
        for item in self._data:
            match = True
            for k, v in filter_dict.items():
                if k == "$or" and isinstance(v, list):
                    or_match = any(all(item.get(ok) == ov for ok, ov in cond.items()) for cond in v)
                    if not or_match:
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(item)
        
        if sort:
            # Simple sorting by first sort key
            field, direction = sort[0]
            reverse = direction < 0
            results.sort(key=lambda x: str(x.get(field, "")), reverse=reverse)
            
        if limit > 0:
            results = results[:limit]
        return results

    def find_one(self, filter_dict: Dict[str, Any]):
        res = self.find(filter_dict, limit=1)
        return res[0] if res else None

    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        for item in self._data:
            match = all(item.get(k) == v for k, v in filter_dict.items())
            if match:
                if "$set" in update_dict:
                    item.update(update_dict["$set"])
                if "$push" in update_dict:
                    for pk, pv in update_dict["$push"].items():
                        if pk not in item:
                            item[pk] = []
                        if isinstance(item[pk], list):
                            item[pk].append(pv)
                self._save()
                return type("UpdateResult", (), {"modified_count": 1})()
        return type("UpdateResult", (), {"modified_count": 0})()

    def delete_one(self, filter_dict: Dict[str, Any]):
        for i, item in enumerate(self._data):
            if all(item.get(k) == v for k, v in filter_dict.items()):
                self._data.pop(i)
                self._save()
                return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()

    def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None):
        return len(self.find(filter_dict))


class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_atlas_connected = False
        self._collections: Dict[str, Any] = {}
        self.connect()

    def connect(self):
        try:
            from pymongo import MongoClient
            import certifi
            
            logger.info("Attempting connection to MongoDB Atlas...")
            self.client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
                socketTimeoutMS=2000,
                maxPoolSize=50,
                minPoolSize=1,
                retryWrites=True,
                tlsCAFile=certifi.where() if hasattr(certifi, 'where') else None
            )
            self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            self.is_atlas_connected = True
            logger.info("Successfully connected to MongoDB Atlas!")
        except Exception as e:
            logger.warning(f"MongoDB Atlas connection unvailable ({e}). Activating persistent JSON local database engine fallback.")
            self.is_atlas_connected = False
            self.db = None

    def get_collection(self, name: str):
        if self.is_atlas_connected and self.db is not None:
            try:
                return self.db[name]
            except Exception as e:
                logger.error(f"Error accessing collection {name} in MongoDB: {e}")
        
        # Fallback collection
        if name not in self._collections:
            self._collections[name] = LocalJSONCollection(name)
        return self._collections[name]


db_manager = DatabaseManager()

# Pre-defined collection accessors
def get_complaints_col():
    return db_manager.get_collection("complaints")

def get_knowledge_col():
    return db_manager.get_collection("knowledge_documents")

def get_chunks_col():
    return db_manager.get_collection("document_chunks")

def get_rules_col():
    return db_manager.get_collection("rule_matrix")

def get_escalation_rules_col():
    return db_manager.get_collection("escalation_rules")

def get_audit_logs_col():
    return db_manager.get_collection("audit_logs")

def get_users_col():
    return db_manager.get_collection("users")

def get_live_chats_col():
    return db_manager.get_collection("live_chats")
