import os
from typing import List, Dict, Any, Optional

PRODUCTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "products_50.txt")

class ProductCatalog:
    _cached_products: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def get_all_products(cls) -> List[Dict[str, Any]]:
        if cls._cached_products is not None:
            return cls._cached_products
        
        products = []
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 5:
                        products.append({
                            "product_id": parts[0],
                            "product_name": parts[1],
                            "category": parts[2],
                            "warranty": parts[3],
                            "price": parts[4]
                        })
        cls._cached_products = products
        return products

    @classmethod
    def find_product(cls, identifier: str) -> Optional[Dict[str, Any]]:
        identifier = identifier.strip().upper()
        for p in cls.get_all_products():
            if p["product_id"].upper() == identifier or identifier in p["product_name"].upper():
                return p
        return None
