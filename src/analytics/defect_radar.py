from collections import Counter
from typing import Any, Dict, List

from src.products.catalog import ProductCatalog


class DefectRadarEngine:
    @classmethod
    def generate_defect_radar(cls, complaints_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        products = ProductCatalog.get_all_products()
        indexed_products = []
        for product in products:
            indexed_products.append({
                **product,
                "normalized_id": str(product.get("product_id", "")).casefold(),
                "normalized_name": str(product.get("product_name", "")).casefold(),
                "complaint_count": 0,
                "mention_modes": Counter(),
            })

        matched_count = 0
        for complaint in complaints_list:
            product_text = str(complaint.get("product_or_service", "")).casefold()
            matching = [
                product for product in indexed_products
                if product["normalized_id"] and product["normalized_id"] in product_text
                or product["normalized_name"] and product["normalized_name"] in product_text
            ]
            if not matching:
                continue
            product = max(matching, key=lambda item: len(item["normalized_name"]))
            product["complaint_count"] += 1
            matched_count += 1
            complaint_text = " ".join((
                str(complaint.get("complaint_title", "")),
                str(complaint.get("complaint_description", "")),
            )).casefold()
            product["mention_modes"][cls._classify_mention(complaint_text)] += 1

        monitored_products = []
        for product in indexed_products:
            modes = product["mention_modes"]
            monitored_products.append({
                "product_id": product.get("product_id", "Not recorded"),
                "name": product.get("product_name", "Unnamed product"),
                "category": product.get("category", "Not recorded"),
                "price": product.get("price"),
                "complaint_count": product["complaint_count"],
                "primary_mention_type": modes.most_common(1)[0][0] if modes else "No matched complaints",
            })

        monitored_products.sort(key=lambda product: (-product["complaint_count"], product["name"]))
        return {
            "catalog_product_count": len(indexed_products),
            "complaints_received": len(complaints_list),
            "complaints_matched_to_catalog": matched_count,
            "complaints_without_catalog_match": len(complaints_list) - matched_count,
            "monitored_products": monitored_products,
            "matching_basis_note": "Counts are complaint references matched by product ID or catalog name; they are not failure rates, reliability scores, or recall decisions.",
        }

    @staticmethod
    def _classify_mention(text: str) -> str:
        keyword_groups = {
            "Display": ("screen", "display", "pixel", "glass", "crack"),
            "Battery/Power": ("battery", "charge", "swelling", "power", "drain"),
            "Firmware/Software": ("boot", "freeze", "crash", "firmware", "bluetooth", "update"),
            "Thermal": ("heat", "hot", "thermal", "warm", "fan"),
            "Audio/Cosmetic": ("audio", "sound", "cosmetic", "scratch", "appearance"),
        }
        for mode, keywords in keyword_groups.items():
            if any(keyword in text for keyword in keywords):
                return mode
        return "Unspecified"
