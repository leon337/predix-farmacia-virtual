from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://dados.anvisa.gov.br/dados/TA_PRODUTO_SAUDE_SITE.csv"
TARGET_COUNT = 500
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "real_products.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-REAL-001" / "SOURCE-REPORT.md"

COLUMN_ALIASES = {
    "registration": ["NUMERO_REGISTRO_CADASTRO", "NUMERO_REGISTRO", "REGISTRO_ANVISA"],
    "commercial": ["NOME_COMERCIAL", "NOME_PRODUTO", "PRODUTO"],
    "technical": ["NOME_TECNICO", "NOME_TÉCNICO", "DESCRICAO_TECNICA"],
    "model": ["MODELO_PRODUTO", "MODELO", "NOME_MODELO", "APRESENTACAO_MODELO"],
    "manufacturer": ["FABRICANTE_LEGAL", "NOME_FABRICANTE", "FABRICANTE"],
    "holder": ["DETENTOR_REGISTRO_CADASTRO", "DETENTOR_REGISTRO", "EMPRESA_DETENTORA"],
    "country": ["PAIS_FABRICANTE", "PAÍS_FABRICANTE", "PAIS"],
    "risk": ["CLASSE_RISCO", "CLASSE_R", "RISCO"],
    "updated": ["DT_ATUALIZACAO_DADO", "DATA_ATUALIZACAO", "DT_ATUALIZACAO"],
}

ALLOW = {
    "Termômetros": ["TERMOMETRO", "TERMÔMETRO"],
    "Oxímetros": ["OXIMETRO", "OXÍMETRO"],
    "Pressão arterial": ["MEDIDOR DE PRESSAO", "MEDIDOR DE PRESSÃO", "ESFIGMOMANOMETRO", "ESFIGMOMANÔMETRO"],
    "Glicemia": ["GLICOSIMETRO", "GLICOSÍMETRO", "MEDIDOR DE GLICOSE", "TIRA REAGENTE", "LANCETA"],
    "Curativos": ["CURATIVO", "GAZE", "COMPRESSA", "ATADURA", "BANDAGEM", "ESPARADRAPO", "MICROPOROSA"],
    "Proteção respiratória": ["MASCARA", "MÁSCARA", "RESPIRADOR"],
    "Luvas": ["LUVA DE PROCEDIMENTO", "LUVA PARA PROCEDIMENTO", "LUVA NAO CIRURGICA", "LUVA NÃO CIRÚRGICA"],
    "Inalação": ["NEBULIZADOR", "INALADOR"],
    "Terapia térmica": ["BOLSA TERMICA", "BOLSA TÉRMICA", "BOLSA DE GELO", "COMPRESSA TERMICA", "COMPRESSA TÉRMICA"],
    "Ortopedia": ["JOELHEIRA", "TORNOZELEIRA", "MUNHEQUEIRA", "COTOVELEIRA", "IMOBILIZADOR", "MEIA DE COMPRESSAO", "MEIA DE COMPRESSÃO", "PALMILHA ORTOPEDICA", "PALMILHA ORTOPÉDICA", "CINTA ORTOPEDICA", "CINTA ORTOPÉDICA"],
    "Coletores": ["COLETOR DE URINA", "COLETOR UNIVERSAL", "FRASCO COLETOR"],
    "Testes domésticos": ["TESTE DE GRAVIDEZ"],
}

DENY = [
    "MEDICAMENTO", "PRINCIPIO ATIVO", "PRINCÍPIO ATIVO", "CONTROLADO", "ANTIBIOTICO", "ANTIBIÓTICO",
    "IMPLANTE", "PROTESE", "PRÓTESE", "STENT", "CATETER", "SONDA", "BISTURI", "AGULHA", "SERINGA",
    "EQUIPO", "CANULA", "CÂNULA", "CIRURGICO", "CIRÚRGICO", "ENDOSCOP", "ANESTESIA", "HEMODIALISE",
    "HEMODIÁLISE", "VENTILADOR PULMONAR", "MARCAPASSO", "DESFIBRILADOR", "CARDIOVERSOR", "ENDOPROTESE",
    "ENDOPRÓTESE", "USO EXCLUSIVO HOSPITALAR", "USO HOSPITALAR", "LABORATORIO CLINICO", "LABORATÓRIO CLÍNICO",
]


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).strip().upper()


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ;,-")


def download() -> bytes:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Predix-Farmacia-Virtual/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if len(data) < 1_000_000:
        raise RuntimeError(f"Arquivo oficial inesperadamente pequeno: {len(data)} bytes")
    return data


def decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError("Não foi possível decodificar o CSV oficial")


def resolve_columns(headers: list[str]) -> dict[str, str | None]:
    normalized = {norm(header): header for header in headers}
    result: dict[str, str | None] = {}
    for field, aliases in COLUMN_ALIASES.items():
        result[field] = next((normalized[norm(alias)] for alias in aliases if norm(alias) in normalized), None)
    required = ["registration", "technical", "manufacturer"]
    missing = [field for field in required if not result[field]]
    if missing:
        raise RuntimeError(f"Colunas obrigatórias ausentes: {missing}; cabeçalhos={headers}")
    return result


def get(row: dict[str, str], columns: dict[str, str | None], field: str) -> str:
    column = columns.get(field)
    return clean(row.get(column, "")) if column else ""


def category_for(text: str) -> str | None:
    normalized = norm(text)
    if any(norm(term) in normalized for term in DENY):
        return None
    for category, terms in ALLOW.items():
        if any(norm(term) in normalized for term in terms):
            return category
    return None


def make_name(commercial: str, technical: str, model: str) -> str:
    base = commercial if commercial and norm(commercial) not in {"NAO INFORMADO", "N/A", "SEM NOME"} else technical
    if model and norm(model) not in norm(base) and len(model) <= 120:
        return clean(f"{base} — {model}")[:220]
    return clean(base)[:220]


def build(rows: csv.DictReader[str]) -> tuple[list[dict[str, object]], dict[str, object]]:
    headers = list(rows.fieldnames or [])
    columns = resolve_columns(headers)
    products: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    scanned = 0
    rejected = 0
    source_updated = ""

    for row in rows:
        scanned += 1
        registration = get(row, columns, "registration")
        commercial = get(row, columns, "commercial")
        technical = get(row, columns, "technical")
        model = get(row, columns, "model")
        manufacturer = get(row, columns, "manufacturer") or get(row, columns, "holder")
        country = get(row, columns, "country")
        risk = get(row, columns, "risk")
        updated = get(row, columns, "updated")
        source_updated = max(source_updated, updated)

        combined = " | ".join([commercial, technical, model])
        category = category_for(combined)
        name = make_name(commercial, technical, model)
        key = (norm(registration), norm(name), norm(manufacturer))

        if not registration or not name or not manufacturer or not category or key in seen:
            rejected += 1
            continue

        seen.add(key)
        products.append({
            "id": len(products) + 1,
            "sku": f"ANVISA-{re.sub(r'[^0-9A-Za-z]', '', registration)}-{len(products)+1:04d}",
            "name": name,
            "category": category,
            "manufacturer": manufacturer[:220],
            "activeIngredient": None,
            "presentation": technical[:220] or model[:220] or "Produto para saúde",
            "priceCents": None,
            "prescriptionRequired": False,
            "isDemo": True,
            "anvisaRegistration": registration,
            "sourceUrl": SOURCE_URL,
            "sourceUpdatedAt": updated or None,
            "country": country or None,
            "riskClass": risk or None,
        })
        if len(products) == TARGET_COUNT:
            break

    if len(products) != TARGET_COUNT:
        raise RuntimeError(f"Foram encontrados apenas {len(products)} produtos elegíveis; esperado={TARGET_COUNT}")

    meta = {
        "sourceUrl": SOURCE_URL,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceUpdatedAt": source_updated or None,
        "scannedRows": scanned,
        "rejectedRows": rejected,
        "acceptedRows": len(products),
        "columns": columns,
        "filters": {"allowCategories": list(ALLOW), "denyTerms": DENY},
    }
    return products, meta


def main() -> int:
    raw = download()
    source_sha = hashlib.sha256(raw).hexdigest()
    text = decode(raw)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    products, meta = build(reader)
    meta["sourceSha256"] = source_sha

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "products": products}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Relatório de origem — catálogo real\n\n"
        f"- Fonte oficial: `{SOURCE_URL}`\n"
        f"- SHA-256 do CSV: `{source_sha}`\n"
        f"- SHA-256 do catálogo: `{catalog_sha}`\n"
        f"- Linhas examinadas: `{meta['scannedRows']}`\n"
        f"- Linhas rejeitadas: `{meta['rejectedRows']}`\n"
        f"- Produtos aceitos: `{meta['acceptedRows']}`\n"
        f"- Gerado em: `{meta['generatedAt']}`\n"
        f"- Atualização informada pela fonte: `{meta['sourceUpdatedAt']}`\n\n"
        "Os produtos possuem identidade e registro reais. Estoque, reservas, clientes e demais operações continuam simulados.\n",
        encoding="utf-8",
    )

    print(json.dumps({"catalog": str(OUTPUT), "products": len(products), "source_sha256": source_sha, "catalog_sha256": catalog_sha}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
