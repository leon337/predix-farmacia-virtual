from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from build_retail_catalog_with_images import (
    CARE_TERMS,
    FOOD_TERMS,
    HOUSEHOLD_TERMS,
    MEDICINE_TERMS,
    QUANTITY_ONLY,
    normalized,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "retail_products_with_images.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-IMAGES-001" / "SOURCE-REPORT.md"


def main() -> int:
    raw = CATALOG.read_bytes()
    payload = json.loads(raw)
    products = payload["products"]
    meta = payload["meta"]
    report = REPORT.read_text(encoding="utf-8")
    digest = hashlib.sha256(raw).hexdigest()

    assert len(products) == 500
    assert meta["acceptedProducts"] == 500
    assert meta["distinctProducts"] == 500
    assert meta["productsWithImages"] == 500
    assert meta["stockUnitsAreSeparate"] is True
    assert meta["operationsAreSimulated"] is True
    assert meta["pricesAreUnavailable"] is True
    assert meta["scopePolicy"] == "personal-care-positive-signal; food-medicine-household-denylist"
    assert meta["scopeEvidencePersisted"] is True
    assert digest in report

    assert len({p["id"] for p in products}) == 500
    assert len({p["sku"] for p in products}) == 500
    assert len({p["barcode"] for p in products}) == 500
    assert len({(p["name"].casefold(), p["manufacturer"].casefold()) for p in products}) == 500

    for product in products:
        evidence = str(product.get("scopeEvidence") or "").strip()
        searchable = normalized(" ".join((product["name"], product["category"], evidence)))
        normalized_evidence = normalized(evidence)
        assert re.fullmatch(r"\d{8,14}", product["barcode"]), product
        assert product["name"] and product["manufacturer"] and product["category"], product
        assert evidence, product
        assert not FOOD_TERMS.search(searchable), product
        assert not MEDICINE_TERMS.search(searchable), product
        assert not HOUSEHOLD_TERMS.search(searchable), product
        assert CARE_TERMS.search(normalized_evidence), product
        assert not QUANTITY_ONLY.fullmatch(product["manufacturer"]), product
        assert urlparse(product["imageUrl"]).hostname == "images.openbeautyfacts.org", product
        assert product["imageSource"] == "Open Beauty Facts", product
        assert product["sourceDataset"] == "Open Beauty Facts", product
        assert product["priceCents"] is None, product
        assert product["identityReal"] is True, product
        assert product["operationsSimulated"] is True, product
        assert product["prescriptionRequired"] is False, product

    print(
        json.dumps(
            {
                "status": "PASS",
                "productRecords": 500,
                "distinctProducts": 500,
                "productsWithImages": 500,
                "productsWithScopeEvidence": 500,
                "blockedProducts": 0,
                "catalogSha256": digest,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
