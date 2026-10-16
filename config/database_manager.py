import logging
import os
from typing import Any, Dict

from config.local_json import LocalJSONCollection
from config.settings import settings


logger = logging.getLogger("SupportNova.Database")


class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_atlas_connected = False
        self._collections: Dict[str, Any] = {}
        self.connect()

    def connect(self):
        if not settings.MONGODB_URI:
            if settings.PUBLIC_DEMO_MODE:
                raise RuntimeError("PUBLIC_DEMO_MODE requires its isolated MongoDB database; local JSON fallback is disabled.")
            if os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RENDER"):
                raise RuntimeError("MONGODB_URI must be configured for hosted deployments to prevent ephemeral data loss.")
            logger.info("MONGODB_URI is not configured. Using the persistent local JSON database.")
            return
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
                tlsCAFile=certifi.where() if hasattr(certifi, "where") else None,
            )
            self.client.admin.command("ping")
            self.db = self.client[settings.DATABASE_NAME]
            self.is_atlas_connected = True
            logger.info("Successfully connected to MongoDB Atlas!")
        except Exception as error:
            logger.warning(f"MongoDB Atlas connection unavailable ({error}).")
            self.is_atlas_connected = False
            self.db = None
            if settings.PUBLIC_DEMO_MODE:
                raise RuntimeError("MongoDB is unavailable for PUBLIC_DEMO_MODE; refusing to use any local or shared data store.") from error
            if os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RENDER"):
                raise RuntimeError("MongoDB is unavailable in the hosted environment; refusing to start with an ephemeral database.") from error

    def get_collection(self, name: str):
        if self.is_atlas_connected and self.db is not None:
            try:
                return self.db[name]
            except Exception as error:
                logger.error(f"Error accessing collection {name} in MongoDB: {error}")
        if name not in self._collections:
            self._collections[name] = LocalJSONCollection(name)
        return self._collections[name]
