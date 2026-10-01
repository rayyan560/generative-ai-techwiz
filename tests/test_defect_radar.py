from src.analytics import defect_radar


def test_product_complaint_summary_only_counts_catalog_matches(monkeypatch):
    monkeypatch.setattr(
        defect_radar.ProductCatalog,
        "get_all_products",
        lambda: [{"product_id": "NV-01", "product_name": "NovaBook Pro 16", "category": "Laptop", "price": 999.0}],
    )

    result = defect_radar.DefectRadarEngine.generate_defect_radar([
        {"product_or_service": "NovaBook Pro 16 Laptop", "complaint_title": "Screen cracked"},
        {"product_or_service": "novabook pro 16", "complaint_title": "Battery drains"},
        {"product_or_service": "Unknown device", "complaint_title": "Screen cracked"},
    ])

    assert result["complaints_received"] == 3
    assert result["complaints_matched_to_catalog"] == 2
    assert result["complaints_without_catalog_match"] == 1
    assert result["monitored_products"][0]["complaint_count"] == 2
    assert result["monitored_products"][0]["primary_mention_type"] == "Display"
    assert "geo_spatial_distribution" not in result
    assert "automated_recall_advisory" not in result
