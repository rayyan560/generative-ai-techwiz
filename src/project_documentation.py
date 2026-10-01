import json
from pathlib import Path


def load_topic_details():
    details_dir = Path(__file__).with_name("documentation_topics")
    details = {}
    for data_file in sorted(details_dir.glob("*.json")):
        details.update(json.loads(data_file.read_text(encoding="utf-8")))
    return details


ADDITIONAL_TOPIC_DETAILS = load_topic_details()
