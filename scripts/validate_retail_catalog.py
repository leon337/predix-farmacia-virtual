from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "retail_products_with_images.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-IMAGES-001" / "SOURCE-REPORT.md"

BLOCKED = re.compile(
    r"\b(rooibos|advil|antacid|antiacid|tablet|tablets|comprimido|comprimidos|capsule|capsules|c[aá]psula|c[aá]psulas|syrup|xarope|medicine|medication|medicament|m[eé]dicament|ibuprofen|ibuprofeno|aspirin|aspirina|acetaminophen|paracetamol|analgesic|analg[eé]sico|pain relief|allergy relief|antifungal|anti fungal|antif[uú]ngico|laxative|laxante|suppository|suposit[oó]rio|nicotine|nicotina|cbd|thc|sleep aid|sleeping pills|cough syrup|cold and flu|bathroom tissue|toilet paper|paper towel|papel higi[eê]nico|papel toalha|laundry|detergent|dish soap|dishwashing|bleach|floor cleaner|surface cleaner|trash bag|garbage bag|p[aã]o|arroz|feij[aã]o|milho|farinha|biscoit|bolach|chocolate|caf[eé]|coffee|tea|leite|milk|queijo|iogurte|manteiga|margarina|macarr[aã]o|massa|bolo|sorvete|pizza|hamb[uú]rguer|sandu[ií]che|carne|frango|peixe|lingui[cç]a|cerveja|vinho|refrigerante|suco|juice|bebida|drink|snack|cereal|granola|a[cç][uú]car|sugar|tempero|molho|doce|bombom|geleia)\b",
    re.IGNORECASE,
)
CARE = re.compile(
    r"\b(shampoo|conditioner|acondicionador|condicionador|hair mask|hair cream|hair oil|hair gel|hair spray|hair serum|cabelo|capilar|cheveux|capillaire|scalp|soap|sabonete|savon|shower gel|gel douche|body wash|deodorant|d[eé]odorant|antiperspirant|anti transpirant|toothpaste|dentifrice|mouthwash|bain de bouche|oral rinse|cream|cr[eè]me|creme|hidratante|moisturizer|moisturiser|moisturizing|lotion|lo[cç][aã]o|serum|s[eé]rum|cleanser|cleansing|nettoyant|face wash|facial|visage|face cream|body cream|body lotion|corps|body care|skin care|skincare|skin|peau|derm|sunscreen|sun cream|solar|solaire|spf|fps|after sun|mask|masque|m[aá]scara facial|makeup|maquillage|lipstick|batom|foundation|concealer|blush|mascara|nail polish|nail care|esmalte|removedor|ongle|perfume|parfum|eau de toilette|eau de parfum|cologne|col[oô]nia|shaving|aftershave|rasage|barba|beard|balm|baume|lip balm|l[eè]vres|acne|exfoliant|scrub|esfoliante|hand cream|hand soap|mains|m[aã]os|dental floss|fio dental|toothbrush|escova dental|oral care|dental care|hygiene|hygi[eè]ne|cosmetic|cosm[eé]tique|baby shampoo|baby lotion|baby wash|bebe|beb[eê]|diaper cream|assadura)\b",
    re.IGNORECASE,
)
QUANTITY_ONLY = re.compile(r"^\s*\d+(?:[.,]\d+)?\s*(?:mg|g|kg|ml|cl|dl|l|un|unid|unidade|unidades)?\s*$", re.IGNORECASE)


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
    assert digest in report

    assert len({p["id"] for p in products}) == 500
    assert len({p["sku"] for p in products}) == 500
    assert len({p["barcode"] for p in products}) == 500
    assert len({(p["name"].casefold(), p["manufacturer"].casefold()) for p in products}) == 500

    for product in products:
        searchable = " ".join((product["name"], product["category"]))
        assert re.fullmatch(r"\d{8,14}", product["barcode"]), product
        assert product["name"] and product["manufacturer"] and product["category"], product
        assert not BLOCKED.search(searchable), product
        assert CARE.search(searchable), product
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
                "blockedProducts": 0,
                "catalogSha256": digest,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
