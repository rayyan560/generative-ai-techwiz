from fastapi import APIRouter

from src.products.catalog import ProductCatalog


router = APIRouter(prefix="/api", tags=["Product Catalog"])


@router.get("/products")
async def get_products():
    products = ProductCatalog.get_all_products()
    return {"products": products, "total": len(products)}
