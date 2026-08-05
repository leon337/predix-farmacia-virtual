from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TARGET_COUNT = 500
CANDIDATE_LIMIT = 16000
IMAGE_WORKERS = 12
IMAGE_BATCH_SIZE = 240
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "retail_products_with_images.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-IMAGES-001" / "SOURCE-REPORT.md"
DUMP_URL = "https://static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv"
IMAGE_SOURCE = "Open Beauty Facts"
IMAGE_HOST = "images.openbeautyfacts.org"
USER_AGENT = "PredixFarmaciaVirtual/1.0 (https://github.com/leon337/predix-farmacia-virtual)"

FOOD_TERMS = re.compile(
    r"\b(p[aã]o|arroz|feij[aã]o|milho|farinha|biscoit|bolach|chocolate|caf[eé]|coffee|tea|rooibos|leite|milk|queijo|iogurte|manteiga|margarina|macarr[aã]o|massa|bolo|sorvete|pizza|hamb[uú]rguer|sandu[ií]che|carne|frango|peixe|lingui[cç]a|cerveja|vinho|refrigerante|suco|juice|bebida|drink|snack|cereal|granola|a[cç][uú]car|sugar|tempero|molho|doce|bombom|geleia)\b",
    re.IGNORECASE,
)
MEDICINE_TERMS = re.compile(
    r"\b(advil|antacids?|antiacids?|tablets?|comprimidos?|capsules?|c[aá]psulas?|syrup|xarope|medicine|medication|medicament|m[eé]dicament|ibuprofen|ibuprofeno|aspirin|aspirina|acetaminophen|paracetamol|analgesic|analg[eé]sico|pain relief|allergy relief|antifungal|anti fungal|antif[uú]ngico|laxative|laxante|suppository|suposit[oó]rio|nicotine|nicotina|cbd|thc|sleep aid|sleeping pills|cough syrup|cold and flu)\b",
    re.IGNORECASE,
)
HOUSEHOLD_TERMS = re.compile(
    r"\b(bathroom tissue|toilet paper|paper towel|papel higi[eê]nico|papel toalha|laundry|detergent|dish soap|dishwashing|bleach|floor cleaner|surface cleaner|trash bag|garbage bag)\b",
    re.IGNORECASE,
)
CARE_TERMS = re.compile(
    r"\b(shampoos?|conditioners?|acondicionadores?|condicionadores?|hair masks?|hair creams?|hair oils?|hair gels?|hair sprays?|hair serums?|cabelo|capilar|cheveux|capillaire|scalp|soaps?|sabonetes?|savon|shower gels?|gel douche|body wash|deodorants?|d[eé]odorants?|antiperspirants?|anti transpirant|toothpastes?|dentifrice|mouthwashes?|bain de bouche|oral rinse|creams?|cr[eè]mes?|cremes?|hidratantes?|moisturizers?|moisturisers?|moisturizing|lotions?|lo[cç][aã]o|serums?|s[eé]rums?|cleansers?|cleansing|nettoyant|face wash|facial|visage|face creams?|body creams?|body lotions?|corps|body care|skin care|skincare|skin|peau|derm|sunscreens?|sun creams?|solar|solaire|spf|fps|after sun|masks?|masque|m[aá]scara facial|makeup|maquillage|lipsticks?|batom|foundations?|concealers?|blush|mascara|nail polish|nail care|esmalte|removedor|ongle|perfumes?|parfum|eau de toilette|eau de parfum|colognes?|col[oô]nia|shaving|aftershave|rasage|barba|beard|balms?|baume|lip balms?|l[eè]vres|acne|exfoliant|scrub|esfoliante|hand creams?|hand soaps?|mains|m[aã]os|dental floss|fio dental|toothbrushes?|escova dental|oral care|dental care|hygiene|hygi[eè]ne|cosmetics?|cosmetic products?|cosm[eé]tique|baby shampoo|baby lotion|baby wash|bebe|beb[eê]|diaper cream|assadura)\b",
    re.IGNORECASE,
)
GENERIC_CATEGORIES = re.compile(
    r"^(open beauty facts|non food products|non alimentaire|productos no alimenticios|incorrect product type|higiene e cuidados pessoais|hygiene|hygi[eè]ne)$",
    re.IGNORECASE,
)
QUANTITY_ONLY = re.compile(
    r"^\s*\d+(?:[.,]\d+)?\s*(?:mg|g|kg|ml|cl|dl|l|un|unid|unidade|unidades)?\s*$",
    re.IGNORECASE,
)
DIGITS_ONLY = re.compile(r"^\d{8,14}$")


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ;,-")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).strip().lower()


def valid_barcode(value: str) -> bool:
    return bool(re.fullmatch(r"\d{8,14}", value))


def valid_brand(value: str) -> bool:
    return bool(re.search(r"[A-Za-zÀ-ÿ]", value)) and not QUANTITY_ONLY.fullmatch(value)


def first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = clean(row.get(key))
        if value:
            return value
    return ""


def raw_categories(row: dict[str, str]) -> str:
    return first_value(
        row,
        "categories",
        "categories_en",
        "categories_tags",
        "main_category",
        "main_category_en",
    )


def scope_text(name: str, row: dict[str, str]) -> str:
    categories = raw_categories(row)
    category_parts = [
        clean(part.split(":")[-1].replace("-", " "))
        for part in categories.split(",")
        if clean(part)
    ]
    specific = [part for part in category_parts if not GENERIC_CATEGORIES.fullmatch(part)]
    return clean(" ".join([name, *specific]))[:1000]


def valid_scope(evidence: str, name: str) -> bool:
    candidate = normalized(evidence)
    if DIGITS_ONLY.fullmatch(clean(name)):
        return False
    if (
        FOOD_TERMS.search(candidate)
        or MEDICINE_TERMS.search(candidate)
        or HOUSEHOLD_TERMS.search(candidate)
    ):
        return False
    return bool(CARE_TERMS.search(candidate))


def valid_image_url(value: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(value)
        return parsed.scheme == "https" and parsed.hostname == IMAGE_HOST and bool(parsed.path)
    except ValueError:
        return False


def image_is_reachable(url: str, timeout: int = 20) -> bool:
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Range": "bytes=0-2047",
                "Accept": "image/*",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "").lower()
            return response.status in {200, 206} and content_type.startswith("image/")
    except Exception:
        return False


def category_from(row: dict[str, str]) -> str:
    categories = raw_categories(row)
    if categories:
        for part in categories.split(","):
            raw = clean(part.split(":")[-1].replace("-", " "))
            if raw and not GENERIC_CATEGORIES.fullmatch(raw):
                return raw.title()[:120]
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
        "outsideCareScope": 0,
        "invalidBrand": 0,
        "invalidImageHost": 0,
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
                raise RuntimeError(
                    f"Dump incompatível: nenhuma coluna de {group}; cabeçalhos={headers[:40]}"
                )

        for row in reader:
            stats["scanned"] += 1
            code = first_value(row, "code")
            name_pt = first_value(row, "product_name_pt")
            name = name_pt or first_value(row, "product_name")
            brand = first_value(row, "brands")
            image_url = first_value(row, "image_front_url", "image_url")
            evidence = scope_text(name, row)

            if not valid_barcode(code):
                stats["missingCode"] += 1
                continue
            if not name:
                stats["missingName"] += 1
                continue
            if not valid_scope(evidence, name):
                stats["outsideCareScope"] += 1
                continue
            if not brand:
                stats["missingBrand"] += 1
                continue
            if not valid_brand(brand):
                stats["invalidBrand"] += 1
                continue
            if not image_url:
                stats["missingImage"] += 1
                continue
            if not valid_image_url(image_url):
                stats["invalidImageHost"] += 1
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
                    "scopeEvidence": evidence,
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


def verified_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    for start in range(0, len(candidates), IMAGE_BATCH_SIZE):
        batch = candidates[start : start + IMAGE_BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=IMAGE_WORKERS) as executor:
            reachable = executor.map(image_is_reachable, [item["imageUrl"] for item in batch])
            verified.extend(item for item, ok in zip(batch, reachable) if ok)
        if len(verified) >= TARGET_COUNT:
            return verified[:TARGET_COUNT]
    return verified


def build_catalog(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates, stats, headers = parse_dump(path)
    if len(candidates) < TARGET_COUNT:
        raise RuntimeError(f"Candidatos insuficientes: {len(candidates)}; estatísticas={stats}")

    verified = verified_candidates(candidates)
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
                "scopeEvidence": item["scopeEvidence"],
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
        "scopePolicy": "personal-care-positive-signal; food-medicine-household-denylist",
        "scopeEvidencePersisted": True,
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
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    catalog_sha = hashlib.sha256(args.output.read_bytes()).hexdigest()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Relatório de origem — 500 produtos com imagens\n\n"
        f"- Dump oficial: `{DUMP_URL}`\n"
        f"- SHA-256 do dump: `{source_meta['dumpSha256']}`\n"
        f"- Tamanho do dump: `{source_meta['dumpBytes']}` bytes\n"
        f"- Produtos distintos: `{len(products)}`\n"
        f"- Produtos com imagem verificada: `{len(products)}`\n"
        f"- Produtos com evidência de escopo persistida: `{len(products)}`\n"
        f"- SHA-256 do catálogo: `{catalog_sha}`\n"
        f"- Gerado em: `{generated_at}`\n"
        f"- Registros examinados: `{source_meta['statistics']['scanned']}`\n"
        f"- Registros fora do escopo de cuidados pessoais: `{source_meta['statistics']['outsideCareScope']}`\n"
        f"- Fabricantes inválidos excluídos: `{source_meta['statistics']['invalidBrand']}`\n"
        "- Fonte: `Open Beauty Facts`\n"
        "- Identidade: código de barras + nome + marca\n"
        "- Escopo exigido: higiene, beleza e cuidados pessoais\n"
        "- Evidência de escopo: preservada em cada ficha no campo `scopeEvidence`\n"
        "- Medicamentos, alimentos, bebidas e itens domésticos incompatíveis: excluídos\n"
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
                "scopeEvidence": len([product for product in products if product["scopeEvidence"]]),
                "dump_sha256": source_meta["dumpSha256"],
                "catalog_sha256": catalog_sha,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
