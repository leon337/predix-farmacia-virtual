from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

OFFICIAL_SOURCE_URL = "https://dados.anvisa.gov.br/dados/TA_PRODUTO_SAUDE_SITE.csv"
MIRROR_URL = "https://huggingface.co/datasets/Guibiagi/anvisa-rfb-corpus/resolve/main/anvisa_produtos_saude.jsonl"
EXPECTED_MIRROR_SHA256 = "d20df633de53a2c79a2efa03ebae61db72fcb7e27941f23993784f179130f173"
TARGET_COUNT = 500
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "real_products.json"
REPORT = ROOT / "audit" / "MCF-PFV-CATALOG-REAL-001" / "SOURCE-REPORT.md"

ALLOW = {
    "Termômetros": ["TERMOMETRO", "TERMÔMETRO"],
    "Oxímetros": ["OXIMETRO", "OXÍMETRO"],
    "Pressão arterial": ["MEDIDOR DE PRESSAO", "MEDIDOR DE PRESSÃO", "MONITOR DE PRESSAO", "MONITOR DE PRESSÃO", "APARELHO DE PRESSAO", "APARELHO DE PRESSÃO", "ESFIGMOMANOMETRO", "ESFIGMOMANÔMETRO"],
    "Glicemia": ["GLICOSIMETRO", "GLICOSÍMETRO", "MEDIDOR DE GLICOSE", "MONITOR DE GLICOSE", "TIRA REAGENTE PARA GLICOSE", "TIRAS PARA GLICEMIA"],
    "Curativos": ["CURATIVO", "GAZE", "COMPRESSA", "ATADURA", "BANDAGEM", "ESPARADRAPO", "MICROPOROSA", "FITA MICROPOROSA", "ALGODAO HIDROFILO", "ALGODÃO HIDRÓFILO"],
    "Proteção respiratória": ["MASCARA FACIAL", "MÁSCARA FACIAL", "MASCARA DESCARTAVEL", "MÁSCARA DESCARTÁVEL", "RESPIRADOR DESCARTAVEL", "RESPIRADOR DESCARTÁVEL"],
    "Luvas": ["LUVA DE PROCEDIMENTO", "LUVA PARA PROCEDIMENTO", "LUVA NAO CIRURGICA", "LUVA NÃO CIRÚRGICA"],
    "Inalação": ["NEBULIZADOR", "INALADOR"],
    "Terapia térmica": ["BOLSA TERMICA", "BOLSA TÉRMICA", "BOLSA DE GELO", "COMPRESSA TERMICA", "COMPRESSA TÉRMICA"],
    "Ortopedia": ["JOELHEIRA", "TORNOZELEIRA", "MUNHEQUEIRA", "COTOVELEIRA", "IMOBILIZADOR", "MEIA DE COMPRESSAO", "MEIA DE COMPRESSÃO", "PALMILHA ORTOPEDICA", "PALMILHA ORTOPÉDICA", "CINTA ORTOPEDICA", "CINTA ORTOPÉDICA", "TIPOIA", "BENGALA", "MULETA"],
    "Coletores": ["COLETOR DE URINA", "COLETOR UNIVERSAL", "FRASCO COLETOR"],
    "Testes domésticos": ["TESTE DE GRAVIDEZ"],
    "Cuidados nasais": ["ASPIRADOR NASAL", "LAVADOR NASAL"],
    "Incontinência": ["FRALDA PARA INCONTINENCIA", "FRALDA PARA INCONTINÊNCIA", "ABSORVENTE PARA INCONTINENCIA", "ABSORVENTE PARA INCONTINÊNCIA"],
}

DENY = [
    "MEDICAMENTO", "PRINCIPIO ATIVO", "PRINCÍPIO ATIVO", "CONTROLADO", "ANTIBIOTICO", "ANTIBIÓTICO",
    "IMPLANTE", "PROTESE", "PRÓTESE", "STENT", "CATETER", "SONDA", "BISTURI", "AGULHA", "LANCETA",
    "SERINGA", "EQUIPO", "CANULA", "CÂNULA", "CIRURGICO", "CIRÚRGICO", "ENDOSCOP", "ANESTESIA",
    "HEMODIALISE", "HEMODIÁLISE", "VENTILADOR PULMONAR", "MARCAPASSO", "DESFIBRILADOR", "CARDIOVERSOR",
    "ENDOPROTESE", "ENDOPRÓTESE", "USO EXCLUSIVO HOSPITALAR", "USO HOSPITALAR", "LABORATORIO CLINICO",
    "LABORATÓRIO CLÍNICO", "PUNCAO", "PUNÇÃO", "BIOPSIA", "INTRAUTERINO", "INTRAVENOSO", "INTRAVENOSA",
    "OFTALMICO CIRURGICO", "OFTÁLMICO CIRÚRGICO", "ODONTOLOGICO CIRURGICO", "ODONTOLÓGICO CIRÚRGICO",
]

RECORD_RE = re.compile(
    r"^Produto para saúde ANVISA: (?P<name>.+?) "
    r"\(Nome técnico: (?P<technical>.+?)\)\. "
    r"Registro: (?P<registration>[^,]+), Processo: (?P<process>[^.]+)\. "
    r"Classe de risco: (?P<risk>[^.]+)\. "
    r"Detentor: (?P<holder>.+?), CNPJ: (?P<cnpj>\d+)\. "
    r"Fabricante: (?P<manufacturer>.+)\.$"
)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).strip().upper()


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" ;,-")


def category_for(text: str) -> str | None:
    normalized = norm(text)
    if any(norm(term) in normalized for term in DENY):
        return None
    for category, terms in ALLOW.items():
        if any(norm(term) in normalized for term in terms):
            return category
    return None


def parse_jsonl(path: Path) -> tuple[list[dict[str, object]], dict[str, int]]:
    products: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    stats = {"scanned": 0, "invalid_json": 0, "unmatched": 0, "risk_rejected": 0, "filter_rejected": 0, "duplicate": 0}

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stats["scanned"] += 1
            try:
                text = clean(str(json.loads(line).get("text", "")))
            except (json.JSONDecodeError, AttributeError):
                stats["invalid_json"] += 1
                continue
            match = RECORD_RE.match(text)
            if not match:
                stats["unmatched"] += 1
                continue
            fields = {key: clean(value) for key, value in match.groupdict().items()}
            risk = norm(fields["risk"])
            if risk not in {"I", "II", "1", "2"}:
                stats["risk_rejected"] += 1
                continue
            category = category_for(fields["name"] + " | " + fields["technical"])
            if not category:
                stats["filter_rejected"] += 1
                continue
            key = (norm(fields["registration"]), norm(fields["name"]), norm(fields["manufacturer"]))
            if key in seen:
                stats["duplicate"] += 1
                continue
            seen.add(key)
            index = len(products) + 1
            products.append({
                "id": index,
                "sku": f"ANVISA-{re.sub(r'[^0-9A-Za-z]', '', fields['registration'])}-{index:04d}",
                "name": fields["name"][:220],
                "category": category,
                "manufacturer": fields["manufacturer"][:220],
                "activeIngredient": None,
                "presentation": fields["technical"][:220],
                "priceCents": None,
                "prescriptionRequired": False,
                "isDemo": True,
                "anvisaRegistration": fields["registration"],
                "anvisaProcess": fields["process"],
                "registrationHolder": fields["holder"][:220],
                "holderCnpj": fields["cnpj"],
                "sourceUrl": OFFICIAL_SOURCE_URL,
                "sourceMirrorUrl": MIRROR_URL,
                "sourceUpdatedAt": None,
                "riskClass": fields["risk"],
            })
            if len(products) == TARGET_COUNT:
                break

    if len(products) != TARGET_COUNT:
        raise RuntimeError(f"Catálogo incompleto: aceitos={len(products)} esperado={TARGET_COUNT} estatísticas={stats}")
    return products, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    mirror_sha = hashlib.sha256(raw).hexdigest()
    if mirror_sha != EXPECTED_MIRROR_SHA256:
        raise RuntimeError(f"Hash do espelho divergente: {mirror_sha}")

    products, stats = parse_jsonl(args.input)
    generated_at = datetime.now(timezone.utc).isoformat()
    meta = {
        "officialSourceUrl": OFFICIAL_SOURCE_URL,
        "mirrorUrl": MIRROR_URL,
        "mirrorSha256": mirror_sha,
        "generatedAt": generated_at,
        "acceptedRows": len(products),
        "statistics": stats,
        "filters": {"riskClasses": ["I", "II"], "allowCategories": list(ALLOW), "denyTerms": DENY},
        "identityIsReal": True,
        "operationsAreSimulated": True,
        "pricesAreUnavailable": True,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"meta": meta, "products": products}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Relatório de origem — catálogo real\n\n"
        f"- Fonte original declarada: `{OFFICIAL_SOURCE_URL}`\n"
        f"- Espelho versionado: `{MIRROR_URL}`\n"
        f"- SHA-256 validado do espelho: `{mirror_sha}`\n"
        f"- SHA-256 do catálogo gerado: `{catalog_sha}`\n"
        f"- Registros examinados: `{stats['scanned']}`\n"
        f"- Produtos aceitos: `{len(products)}`\n"
        f"- Gerado em: `{generated_at}`\n"
        "- Classes aceitas: `I` e `II`\n"
        "- Medicamentos e itens invasivos/hospitalares: excluídos\n\n"
        "Os nomes, fabricantes, detentores e registros pertencem à base regulatória. Estoque, reservas, clientes e operações permanecem simulados. Preços não foram inventados.\n",
        encoding="utf-8",
    )
    print(json.dumps({"products": len(products), "mirror_sha256": mirror_sha, "catalog_sha256": catalog_sha, "statistics": stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
