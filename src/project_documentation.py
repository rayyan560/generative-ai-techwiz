import json
from pathlib import Path

from src.project_document_catalog import PROJECT_DOCUMENTS, PROJECT_FILES
from src.project_document_topics import PROJECT_TOPIC_DETAILS


def load_topic_details():
    details_dir = Path(__file__).with_name("documentation_topics")
    details = {}
    for data_file in sorted(details_dir.glob("*.json")):
        details.update(json.loads(data_file.read_text(encoding="utf-8")))
    return details


ADDITIONAL_TOPIC_DETAILS = load_topic_details()
TOPIC_DETAILS = {**PROJECT_TOPIC_DETAILS, **ADDITIONAL_TOPIC_DETAILS}


def build_document_sections(document):
    sections = []
    for topic in document["topics"]:
        if topic not in TOPIC_DETAILS:
            raise ValueError(f"Project documentation is missing content for topic: {topic}")
        summary, points = TOPIC_DETAILS[topic]
        sections.append({"title": topic, "summary": summary, "points": points})
    enriched = dict(document)
    enriched["sections"] = sections
    return enriched
