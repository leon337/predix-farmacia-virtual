from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TARGET_COUNT = 500
CANDIDATE_LIMIT = 6000
IMAGE_WORKERS = 12
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "retail_products_with_images.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-IMAGES-001" / "SOURCE-REPORT.md"
DUMP_URL = "https://static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv"
IMAGE_SOURCE = "Open Beauty Facts"
USER_AGENT = "PredixFarmaciaVirtual/1.0 (https://github.com/leon337/predix-farmacia-virtual)"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ;,-")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).strip().lower()


def valid_barcode(value: str) -> bool:
    return bool(re.fullmatch(r"\d{8,14}", value))


def first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = clean(row.get(key))
        if value:
            return value
    return ""


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


def category_from(row: dict[str, str]) -> str:
    categories = first_value(row, "categories", "categories_en", "categories_tags")
    if categories:
        raw = categories.split(",")[0].split(":")[-1].replace("-", " ")
        return clean(raw).title()[:120]
    return "Higiene e cuidados pessoais"


def brazil_priority(row: dict[str, str], name_pt: str) -> int:
    countries = normalized(first_value(row, "countries_tags", "countries", "countries_en"))
    if "brazil" in countries or "brasil" in countries:
        return 0
    if name_pt:
        return 1
    return 2


def parse_dump(path: Path) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    candidates: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    seen_identity: set[tuple[str, str]] = set()
    stats = {
        "scanned": 0,
        "missingCode": 0,
        "missingName": 0,
        "missingBrand": 0,
        "missingImage": 0,
        "duplicates": 0,
    }

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        headers = list(reader.fieldnames or [])
        required_groups = [
            ("code",),
            ("product_name", "product_name_pt"),
            ("brands",),
            ("image_front_url", "image_url"),
        ]
        for group in required_groups:
            if not any(key in headers for key in group):
                raise RuntimeError(f"Dump incompatível: nenhuma coluna de {group}; cabeçalhos={headers[:40]}")

        for row in reader:
            stats["scanned"] += 1
            code = first_value(row, "code")
            name_pt = first_value(row, "product_name_pt")
            name = name_pt or first_value(row, "product_name")
            brand = first_value(row, "brands")
            image_url = first_value(row, "image_front_url", "image_url")

            if not valid_barcode(code):
                stats["missingCode"] += 1
                continue
            if not name:
                stats["missingName"] += 1
                continue
            if not brand:
                stats["missingBrand"] += 1
                continue
            if not image_url.startswith("https://"):
                stats["missingImage"] += 1
                continue

            identity = (normalized(name), normalized(brand))
            if code in seen_codes or identity in seen_identity:
                stats["duplicates"] += 1
                continue
            seen_codes.add(code)
            seen_identity.add(identity)

            candidates.append(
                {
                    "priority": brazil_priority(row, name_pt),
                    "barcode": code,
                    "name": name[:220],
                    "brand": brand[:220],
                    "category": category_from(row),
                    "presentation": first_value(row, "quantity", "product_quantity")[:120]
                    or "Apresentação informada na embalagem",
                    "imageUrl": image_url,
                    "sourceUrl": f"https://world.openbeautyfacts.org/product/{code}",
                }
            )
            if len(candidates) >= CANDIDATE_LIMIT:
                break

    candidates.sort(
        key=lambda item: (
            item["priority"],
            normalized(item["name"]),
            normalized(item["brand"]),
            item["barcode"],
        )
    )
    return candidates, stats, headers


def build_catalog(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates, stats, headers = parse_dump(path)
    if len(candidates) < TARGET_COUNT:
        raise RuntimeError(f"Candidatos insuficientes: {len(candidates)}; estatísticas={stats}")

    with ThreadPoolExecutor(max_workers=IMAGE_WORKERS) as executor:
        reachable = executor.map(image_is_reachable, [item["imageUrl"] for item in candidates])
        verified = [item for item, ok in zip(candidates, reachable) if ok][:TARGET_COUNT]

    if len(verified) != TARGET_COUNT:
        raise RuntimeError(
            f"Catálogo incompleto: imagens verificadas={len(verified)} esperado={TARGET_COUNT}; "
            f"candidatos={len(candidates)}; estatísticas={stats}"
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
                "imageSource": IMAGE_SOURCE,
                "imageVerifiedAt": verified_at,
                "sourceUrl": item["sourceUrl"],
                "sourceDataset": IMAGE_SOURCE,
            }
        )

    metadata = {
        "dumpUrl": DUMP_URL,
        "dumpSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "dumpBytes": path.stat().st_size,
        "headersDetected": headers,
        "statistics": stats,
        "candidates": len(candidates),
    }
    return products, metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    products, source_meta = build_catalog(args.input)
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
            "sources": [IMAGE_SOURCE],
            **source_meta,
        },
        "products": products,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_sha = hashlib.sha256(args.output.read_bytes()).hexdigest()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Relatório de origem — 500 produtos com imagens\n\n"
        f"- Dump oficial: `{DUMP_URL}`\n"
        f"- SHA-256 do dump: `{source_meta['dumpSha256']}`\n"
        f"- Tamanho do dump: `{source_meta['dumpBytes']}` bytes\n"
        f"- Produtos distintos: `{len(products)}`\n"
        f"- Produtos com imagem verificada: `{len(products)}`\n"
        f"- SHA-256 do catálogo: `{catalog_sha}`\n"
        f"- Gerado em: `{generated_at}`\n"
        f"- Registros examinados: `{source_meta['statistics']['scanned']}`\n"
        "- Fonte: `Open Beauty Facts`\n"
        "- Identidade: código de barras + nome + marca\n"
        "- Estoque: separado do cadastro e inteiramente simulado\n"
        "- Preços: ausentes; nenhum valor inventado\n\n"
        "As imagens são URLs frontais de embalagem publicadas pela base aberta. "
        "Cada uma respondeu como conteúdo de imagem durante a geração.\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "products": len(products),
                "distinct": len({product["barcode"] for product in products}),
                "images": len([product for product in products if product["imageUrl"]]),
                "dump_sha256": source_meta["dumpSha256"],
                "catalog_sha256": catalog_sha,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
