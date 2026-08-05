from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TARGET_COUNT = 500
PAGE_SIZE = 100
MAX_PAGES = 20
SEARCH_INTERVAL_SECONDS = 6.5
IMAGE_WORKERS = 12
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "retail_products_with_images.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-IMAGES-001" / "SOURCE-REPORT.md"
API_BASES = (
    "https://world.openbeautyfacts.org/api/v2/search",
    "https://world.openproductsfacts.org/api/v2/search",
)
FIELDS = ",".join(
    [
        "code",
        "product_name",
        "product_name_pt",
        "brands",
        "categories",
        "categories_tags",
        "quantity",
        "image_front_url",
        "image_url",
        "countries_tags",
    ]
)
USER_AGENT = "PredixFarmaciaVirtual/1.0 (https://github.com/leon337/predix-farmacia-virtual)"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ;,-")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).strip().lower()


def valid_barcode(value: str) -> bool:
    return bool(re.fullmatch(r"\d{8,14}", value))


def request_json(url: str, timeout: int = 60) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return json.loads(response.read().decode("utf-8"))


def image_is_reachable(url: str, timeout: int = 20) -> bool:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047", "Accept": "image/*"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "").lower()
            return response.status in {200, 206} and content_type.startswith("image/")
    except Exception:
        return False


def category_from(product: dict[str, Any]) -> str:
    categories = clean(product.get("categories"))
    if categories:
        return categories.split(",")[0][:120]
    tags = product.get("categories_tags") or []
    if isinstance(tags, list) and tags:
        raw = clean(tags[0]).split(":")[-1].replace("-", " ")
        return raw.title()[:120]
    return "Higiene e cuidados pessoais"


def fetch_candidates(base: str, country_filter: bool) -> tuple[list[dict[str, Any]], dict[str, int]]:
    accepted: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    seen_identity: set[tuple[str, str]] = set()
    stats = {
        "pages": 0,
        "scanned": 0,
        "missing_code": 0,
        "missing_name": 0,
        "missing_brand": 0,
        "missing_image": 0,
        "duplicates": 0,
    }

    for page in range(1, MAX_PAGES + 1):
        params: dict[str, str | int] = {
            "page": page,
            "page_size": PAGE_SIZE,
            "fields": FIELDS,
        }
        if country_filter:
            params["countries_tags_en"] = "Brazil"
        url = f"{base}?{urllib.parse.urlencode(params)}"
        payload = request_json(url)
        rows = payload.get("products") or []
        if not rows:
            break
        stats["pages"] += 1
        for raw in rows:
            stats["scanned"] += 1
            code = clean(raw.get("code"))
            name = clean(raw.get("product_name_pt")) or clean(raw.get("product_name"))
            brand = clean(raw.get("brands"))
            image_url = clean(raw.get("image_front_url")) or clean(raw.get("image_url"))
            if not valid_barcode(code):
                stats["missing_code"] += 1
                continue
            if not name:
                stats["missing_name"] += 1
                continue
            if not brand:
                stats["missing_brand"] += 1
                continue
            if not image_url.startswith("https://"):
                stats["missing_image"] += 1
                continue
            identity = (normalized(name), normalized(brand))
            if code in seen_codes or identity in seen_identity:
                stats["duplicates"] += 1
                continue
            seen_codes.add(code)
            seen_identity.add(identity)
            accepted.append(
                {
                    "barcode": code,
                    "name": name[:220],
                    "brand": brand[:220],
                    "category": category_from(raw),
                    "presentation": clean(raw.get("quantity"))[:120] or "Apresentação informada na embalagem",
                    "imageUrl": image_url,
                    "imageSource": "Open Beauty Facts" if "openbeautyfacts" in base else "Open Products Facts",
                    "sourceUrl": (
                        f"https://world.openbeautyfacts.org/product/{code}"
                        if "openbeautyfacts" in base
                        else f"https://world.openproductsfacts.org/product/{code}"
                    ),
                }
            )
            if len(accepted) >= TARGET_COUNT * 2:
                break
        if len(accepted) >= TARGET_COUNT * 2:
            break
        if page < MAX_PAGES:
            time.sleep(SEARCH_INTERVAL_SECONDS)
    return accepted, stats


def build_catalog() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_candidates: list[dict[str, Any]] = []
    combined_stats: dict[str, Any] = {"sources": []}
    seen_codes: set[str] = set()
    seen_identity: set[tuple[str, str]] = set()

    for base in API_BASES:
        for country_filter in (True, False):
            candidates, stats = fetch_candidates(base, country_filter)
            combined_stats["sources"].append(
                {"base": base, "countryFilterBrazil": country_filter, **stats, "candidates": len(candidates)}
            )
            for candidate in candidates:
                identity = (normalized(candidate["name"]), normalized(candidate["brand"]))
                if candidate["barcode"] in seen_codes or identity in seen_identity:
                    continue
                seen_codes.add(candidate["barcode"])
                seen_identity.add(identity)
                all_candidates.append(candidate)
            if len(all_candidates) >= TARGET_COUNT * 2:
                break
        if len(all_candidates) >= TARGET_COUNT * 2:
            break

    all_candidates.sort(key=lambda item: (normalized(item["name"]), normalized(item["brand"]), item["barcode"]))

    with ThreadPoolExecutor(max_workers=IMAGE_WORKERS) as executor:
        reachable = executor.map(image_is_reachable, [item["imageUrl"] for item in all_candidates])
        verified = [item for item, ok in zip(all_candidates, reachable) if ok][:TARGET_COUNT]

    if len(verified) != TARGET_COUNT:
        raise RuntimeError(
            f"Catálogo incompleto: imagens verificadas={len(verified)} esperado={TARGET_COUNT}; "
            f"candidatos={len(all_candidates)}; estatísticas={combined_stats}"
        )

    verified_at = datetime.now(timezone.utc).isoformat()
    products: list[dict[str, Any]] = []
    for index, item in enumerate(verified, start=1):
        products.append(
            {
                "id": index,
                "sku": f"GTIN-{item['barcode']}",
                "barcode": item["barcode"],
                "name": item["name"],
                "category": item["category"],
                "manufacturer": item["brand"],
                "presentation": item["presentation"],
                "priceCents": None,
                "prescriptionRequired": False,
                "identityReal": True,
                "operationsSimulated": True,
                "imageUrl": item["imageUrl"],
                "imageSource": item["imageSource"],
                "imageVerifiedAt": verified_at,
                "sourceUrl": item["sourceUrl"],
                "sourceDataset": item["imageSource"],
            }
        )
    return products, combined_stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    products, stats = build_catalog()
    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "meta": {
            "generatedAt": generated_at,
            "acceptedProducts": len(products),
            "distinctProducts": len({product["barcode"] for product in products}),
            "productsWithImages": len([product for product in products if product["imageUrl"]]),
            "stockUnitsAreSeparate": True,
            "pricesAreUnavailable": True,
            "operationsAreSimulated": True,
            "sources": ["Open Beauty Facts", "Open Products Facts"],
            "statistics": stats,
        },
        "products": products,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_sha = hashlib.sha256(args.output.read_bytes()).hexdigest()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Relatório de origem — 500 produtos com imagens\n\n"
        f"- Produtos distintos: `{len(products)}`\n"
        f"- Produtos com imagem verificada: `{len(products)}`\n"
        f"- SHA-256 do catálogo: `{catalog_sha}`\n"
        f"- Gerado em: `{generated_at}`\n"
        "- Fontes: `Open Beauty Facts` e fallback `Open Products Facts`\n"
        "- Identidade: código de barras + nome + marca\n"
        "- Estoque: separado do cadastro de produtos e inteiramente simulado\n"
        "- Preços: ausentes; nenhum valor inventado\n\n"
        "As imagens são URLs de frente de embalagem publicadas pelas bases abertas. "
        "A presença da imagem foi verificada por HTTP durante a geração.\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "products": len(products),
                "distinct": len({product["barcode"] for product in products}),
                "images": len([product for product in products if product["imageUrl"]]),
                "catalog_sha256": catalog_sha,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
