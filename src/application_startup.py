import json
import logging
import os
import threading

from config.database import get_complaints_col
from src.knowledge_base.manager import KnowledgeBaseManager

logger = logging.getLogger("SupportNova.Startup")


def start_background_initialization(base_dir):
    def initialize():
        try:
            KnowledgeBaseManager.initialize_knowledge_base()
        except Exception:
            logger.error("Knowledge-base initialization failed.")

        try:
            complaints = get_complaints_col()
            if complaints.count_documents({}) == 0:
                dataset_path = os.path.join(base_dir, "sample_complaints", "complaints_500.json")
                if os.path.exists(dataset_path):
                    with open(dataset_path, "r", encoding="utf-8") as source:
                        complaints.insert_many(json.load(source))
        except Exception:
            logger.error("Complaint data initialization failed.")

    logger.info("SupportNova started successfully.")
    threading.Thread(target=initialize, daemon=True).start()
