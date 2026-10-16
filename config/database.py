from config.database_manager import DatabaseManager
from config.local_json import DATA_DIR, LocalJSONCollection, save_json_atomic


db_manager = DatabaseManager()


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
