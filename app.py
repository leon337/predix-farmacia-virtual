from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"
CATALOG_PATH = ROOT / "data" / "real_products.json"
EXPECTED_CATALOG_SHA256 = "322a842080af74e1cafeea0a98f0ea71a930ac442eadb1d6d9911e15b9b7cf34"
DB_PATH = Path(os.environ.get("PREDIX_DATABASE_PATH", ROOT / "data" / "predix.db"))
UTC = timezone.utc

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS company(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  phone TEXT NOT NULL,
  opening_hours TEXT NOT NULL,
  payments TEXT NOT NULL,
  delivery TEXT NOT NULL,
  operations_simulated INTEGER NOT NULL CHECK(operations_simulated=1)
);
CREATE TABLE IF NOT EXISTS products(
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  manufacturer TEXT NOT NULL,
  active_ingredient TEXT,
  presentation TEXT NOT NULL,
  price_cents INTEGER CHECK(price_cents IS NULL OR price_cents>0),
  prescription_required INTEGER NOT NULL CHECK(prescription_required=0),
  anvisa_registration TEXT NOT NULL,
  anvisa_process TEXT,
  registration_holder TEXT,
  holder_cnpj TEXT,
  source_url TEXT NOT NULL,
  source_mirror_url TEXT,
  source_updated_at TEXT,
  risk_class TEXT NOT NULL CHECK(risk_class IN ('I','II','1','2')),
  identity_real INTEGER NOT NULL CHECK(identity_real=1),
  operations_simulated INTEGER NOT NULL CHECK(operations_simulated=1),
  UNIQUE(anvisa_registration,name,manufacturer)
);
CREATE TABLE IF NOT EXISTS inventory(
  product_id INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
  total INTEGER NOT NULL CHECK(total>=0),
  reserved INTEGER NOT NULL DEFAULT 0 CHECK(reserved>=0),
  minimum INTEGER NOT NULL DEFAULT 5 CHECK(minimum>=0),
  updated_at TEXT NOT NULL,
  CHECK(reserved<=total)
);
CREATE TABLE IF NOT EXISTS customers(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  contact TEXT,
  operations_simulated INTEGER NOT NULL CHECK(operations_simulated=1),
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations(
  id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL REFERENCES customers(id),
  status TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  cancelled_at TEXT
);
CREATE TABLE IF NOT EXISTS reservation_items(
  reservation_id TEXT NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity INTEGER NOT NULL CHECK(quantity>0),
  price_cents INTEGER CHECK(price_cents IS NULL OR price_cents>0),
  PRIMARY KEY(reservation_id,product_id)
);
CREATE TABLE IF NOT EXISTS conversations(
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  user_message TEXT NOT NULL,
  assistant_message TEXT NOT NULL,
  intent TEXT NOT NULL,
  tool TEXT,
  sources TEXT NOT NULL,
  handoff INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS product_queries(
  id TEXT PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  query_text TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit(
  id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  created_at TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    return con


def load_catalog() -> dict:
    raw = CATALOG_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_CATALOG_SHA256:
        raise RuntimeError(f"Hash do catálogo real divergente: {digest}")
    payload = json.loads(raw.decode("utf-8"))
    products = payload.get("products") or []
    meta = payload.get("meta") or {}
    if len(products) != 500:
        raise RuntimeError(f"Catálogo real inválido: {len(products)} produtos")
    if meta.get("identityIsReal") is not True or meta.get("operationsAreSimulated") is not True:
        raise RuntimeError("Metadados do catálogo real inválidos")
    identities = {
        (str(item.get("anvisaRegistration")), str(item.get("name")), str(item.get("manufacturer")))
        for item in products
    }
    if len(identities) != 500:
        raise RuntimeError("Identidades regulatórias duplicadas")
    if any(
        not item.get("name")
        or not item.get("manufacturer")
        or not item.get("anvisaRegistration")
        or item.get("priceCents") is not None
        or item.get("activeIngredient") is not None
        or item.get("prescriptionRequired") is not False
        for item in products
    ):
        raise RuntimeError("Produto real com campos obrigatórios inválidos")
    return payload


def _old_product_schema(con: sqlite3.Connection) -> bool:
    exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='products'").fetchone()
    if not exists:
        return False
    columns = {row["name"] for row in con.execute("PRAGMA table_info(products)").fetchall()}
    return "identity_real" not in columns or "anvisa_registration" not in columns


def _drop_old_catalog_tables(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys=OFF")
    for table in (
        "reservation_items",
        "reservations",
        "customers",
        "product_queries",
        "inventory",
        "products",
    ):
        con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute("PRAGMA foreign_keys=ON")


def initialize() -> None:
    payload = load_catalog()
    with connect() as con:
        if _old_product_schema(con):
            _drop_old_catalog_tables(con)
        con.executescript(SCHEMA)
        stamp = now()
        con.execute(
            """
            INSERT INTO company(id,name,address,phone,opening_hours,payments,delivery,operations_simulated)
            VALUES(?,?,?,?,?,?,?,1)
            ON CONFLICT(id) DO UPDATE SET
              name=excluded.name,address=excluded.address,phone=excluded.phone,
              opening_hours=excluded.opening_hours,payments=excluded.payments,
              delivery=excluded.delivery,operations_simulated=1
            """,
            (
                "demo-001",
                "Farmácia Horizonte Demo",
                "Avenida Exemplo, 1000 — Recife/PE (fictício)",
                "(81) 3000-0000 (fictício)",
                "Segunda a sábado, 08:00–20:00; domingo, 09:00–14:00",
                "Dinheiro fictício, PIX demonstrativo, débito e crédito simulados",
                "Entregas apenas simuladas, segunda a sábado, 09:00–19:00",
            ),
        )

        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        real_count = con.execute("SELECT COUNT(*) FROM products WHERE identity_real=1").fetchone()[0]
        if count == 500 and real_count == 500:
            return

        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute("DELETE FROM product_queries")
            con.execute("DELETE FROM reservation_items")
            con.execute("DELETE FROM reservations")
            con.execute("DELETE FROM customers")
            con.execute("DELETE FROM inventory")
            con.execute("DELETE FROM products")
            for item in payload["products"]:
                con.execute(
                    """
                    INSERT INTO products(
                      id,sku,name,category,manufacturer,active_ingredient,presentation,
                      price_cents,prescription_required,anvisa_registration,anvisa_process,
                      registration_holder,holder_cnpj,source_url,source_mirror_url,
                      source_updated_at,risk_class,identity_real,operations_simulated
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,1)
                    """,
                    (
                        int(item["id"]),
                        item["sku"],
                        item["name"],
                        item["category"],
                        item["manufacturer"],
                        item.get("activeIngredient"),
                        item["presentation"],
                        item.get("priceCents"),
                        int(bool(item.get("prescriptionRequired"))),
                        item["anvisaRegistration"],
                        item.get("anvisaProcess"),
                        item.get("registrationHolder"),
                        item.get("holderCnpj"),
                        item["sourceUrl"],
                        item.get("sourceMirrorUrl"),
                        item.get("sourceUpdatedAt"),
                        str(item["riskClass"]),
                    ),
                )
                product_id = int(item["id"])
                total = 0 if product_id % 17 == 0 else 12 + (product_id * 37) % 109
                minimum = 3 + product_id % 10
                con.execute(
                    "INSERT INTO inventory(product_id,total,reserved,minimum,updated_at) VALUES(?,?,0,?,?)",
                    (product_id, total, minimum, stamp),
                )
            con.execute(
                "INSERT INTO audit VALUES(?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    "manoel",
                    "REAL_CATALOG_LOADED",
                    "products",
                    None,
                    json.dumps({"products": 500, "catalogSha": EXPECTED_CATALOG_SHA256}),
                    stamp,
                ),
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise


def company(con: sqlite3.Connection) -> dict:
    row = con.execute("SELECT * FROM company LIMIT 1").fetchone()
    return {
        "id": row["id"],
        "name": row["name"],
        "address": row["address"],
        "phone": row["phone"],
        "openingHours": row["opening_hours"],
        "payments": row["payments"],
        "delivery": row["delivery"],
        "identityReal": False,
        "operationsSimulated": True,
    }


def product_dict(row: sqlite3.Row) -> dict:
    available = row["total"] - row["reserved"]
    price_cents = row["price_cents"]
    return {
        "id": row["id"],
        "sku": row["sku"],
        "name": row["name"],
        "category": row["category"],
        "manufacturer": row["manufacturer"],
        "activeIngredient": row["active_ingredient"],
        "presentation": row["presentation"],
        "priceCents": price_cents,
        "price": "Consulte o estabelecimento" if price_cents is None else f"R$ {price_cents/100:.2f}".replace(".", ","),
        "priceAvailable": price_cents is not None,
        "quantityTotal": row["total"],
        "quantityReserved": row["reserved"],
        "quantityAvailable": available,
        "minimum": row["minimum"],
        "prescriptionRequired": False,
        "anvisaRegistration": row["anvisa_registration"],
        "anvisaProcess": row["anvisa_process"],
        "registrationHolder": row["registration_holder"],
        "holderCnpj": row["holder_cnpj"],
        "sourceUrl": row["source_url"],
        "sourceMirrorUrl": row["source_mirror_url"],
        "sourceUpdatedAt": row["source_updated_at"],
        "riskClass": row["risk_class"],
        "identityReal": True,
        "operationsSimulated": True,
    }


def search_products(con: sqlite3.Connection, query: str = "", page: int = 1, page_size: int = 24) -> dict:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    base = "FROM products p JOIN inventory i ON i.product_id=p.id"
    params: list[object] = []
    where = ""
    if query.strip():
        term = f"%{query.strip()}%"
        where = (
            " WHERE p.name LIKE ? COLLATE NOCASE OR p.sku LIKE ? COLLATE NOCASE"
            " OR p.category LIKE ? COLLATE NOCASE OR p.manufacturer LIKE ? COLLATE NOCASE"
            " OR p.presentation LIKE ? COLLATE NOCASE OR p.anvisa_registration LIKE ? COLLATE NOCASE"
        )
        params = [term] * 6
    total = con.execute("SELECT COUNT(*) " + base + where, params).fetchone()[0]
    rows = con.execute(
        "SELECT p.*,i.total,i.reserved,i.minimum " + base + where + " ORDER BY p.name LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()
    return {
        "items": [product_dict(row) for row in rows],
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": (total + page_size - 1) // page_size,
        "identityReal": True,
        "operationsSimulated": True,
        "pricesProvided": False,
    }


def reservation(con: sqlite3.Connection, reservation_id: str) -> dict:
    row = con.execute(
        "SELECT r.*,c.name,c.contact FROM reservations r JOIN customers c ON c.id=r.customer_id WHERE r.id=?",
        (reservation_id,),
    ).fetchone()
    if not row:
        raise ValueError("Reserva não encontrada.")
    items = con.execute(
        "SELECT ri.product_id,p.name,ri.quantity,ri.price_cents FROM reservation_items ri JOIN products p ON p.id=ri.product_id WHERE ri.reservation_id=?",
        (reservation_id,),
    ).fetchall()
    has_missing_price = any(item["price_cents"] is None for item in items)
    total_cents = None if has_missing_price else sum(item["quantity"] * item["price_cents"] for item in items)
    return {
        "id": row["id"],
        "customer": row["name"],
        "status": row["status"],
        "expiresAt": row["expires_at"],
        "createdAt": row["created_at"],
        "items": [dict(item) for item in items],
        "totalCents": total_cents,
        "identityReal": True,
        "operationsSimulated": True,
    }


def create_reservation(con: sqlite3.Connection, payload: dict, key: str) -> dict:
    if not key:
        raise ValueError("Idempotency-Key é obrigatório.")
    old = con.execute("SELECT id FROM reservations WHERE idempotency_key=?", (key,)).fetchone()
    if old:
        return reservation(con, old["id"])
    name = str(payload.get("customerName", "")).strip()
    items = payload.get("items") or []
    if not name or not items:
        raise ValueError("Cliente e itens são obrigatórios.")
    rid, cid, stamp = str(uuid.uuid4()), str(uuid.uuid4()), now()
    expires = (datetime.now(UTC) + timedelta(minutes=60)).replace(microsecond=0).isoformat()
    con.execute("BEGIN IMMEDIATE")
    try:
        selected = []
        for item in items:
            product_id, quantity = int(item["productId"]), int(item["quantity"])
            if quantity <= 0:
                raise ValueError("Quantidade inválida.")
            row = con.execute(
                "SELECT p.name,p.price_cents,i.total,i.reserved FROM products p JOIN inventory i ON i.product_id=p.id WHERE p.id=?",
                (product_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"Produto {product_id} não encontrado.")
            if quantity > row["total"] - row["reserved"]:
                raise ValueError(f"Estoque insuficiente para {row['name']}.")
            selected.append((product_id, quantity, row))
        con.execute("INSERT INTO customers VALUES(?,?,?,?,?)", (cid, name, str(payload.get("contact", "")) or None, 1, stamp))
        con.execute(
            "INSERT INTO reservations(id,customer_id,status,expires_at,idempotency_key,created_at) VALUES(?,?,'ACTIVE',?,?,?)",
            (rid, cid, expires, key, stamp),
        )
        for product_id, quantity, row in selected:
            con.execute(
                "INSERT INTO reservation_items VALUES(?,?,?,?)",
                (rid, product_id, quantity, row["price_cents"]),
            )
            con.execute(
                "UPDATE inventory SET reserved=reserved+?,updated_at=? WHERE product_id=?",
                (quantity, stamp, product_id),
            )
        con.execute(
            "INSERT INTO audit VALUES(?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                "virtual-employee",
                "RESERVATION_CREATED",
                rid,
                None,
                json.dumps(payload, ensure_ascii=False),
                stamp,
            ),
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return reservation(con, rid)


def cancel_reservation(con: sqlite3.Connection, reservation_id: str) -> dict:
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT status FROM reservations WHERE id=?", (reservation_id,)).fetchone()
        if not row:
            raise ValueError("Reserva não encontrada.")
        if row["status"] == "ACTIVE":
            for item in con.execute(
                "SELECT product_id,quantity FROM reservation_items WHERE reservation_id=?",
                (reservation_id,),
            ).fetchall():
                con.execute(
                    "UPDATE inventory SET reserved=reserved-?,updated_at=? WHERE product_id=?",
                    (item["quantity"], now(), item["product_id"]),
                )
            con.execute(
                "UPDATE reservations SET status='CANCELLED',cancelled_at=? WHERE id=?",
                (now(), reservation_id),
            )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return reservation(con, reservation_id)


def clean_term(message: str) -> str:
    text = re.sub(
        r"\b(qual|quanto|custa|preço|preco|valor|tem|estoque|disponível|disponivel|produto|buscar|procure|reservar|reserve|reserva|unidade|unidades|por|favor|do|da|de|o|a|os|as|em)\b",
        " ",
        message,
        flags=re.I,
    )
    return " ".join(re.sub(r"[^\wÀ-ÿ-]+", " ", text).split())


def answer(con: sqlite3.Connection, message: str, session_id: str) -> dict:
    lower = message.casefold()
    sources: list[str] = []
    tool: str | None = None
    handoff = False
    data: dict = {}
    clinical = (
        "dose",
        "dosagem",
        "posologia",
        "diagnóstico",
        "diagnostico",
        "sintoma",
        "tratamento",
        "o que devo tomar",
        "qual remédio",
        "qual remedio",
    )
    if any(term in lower for term in clinical):
        intent, tool, handoff = "clinical_handoff", "safety_policy", True
        reply = "Não posso orientar diagnóstico, tratamento, dosagem ou uso de medicamentos. A solicitação deve ser tratada por farmacêutico ou profissional de saúde humano."
        sources = ["treinamento/politicas.md"]
    elif any(term in lower for term in ("olá", "ola", "oi", "bom dia", "boa tarde", "boa noite")):
        info = company(con)
        intent, tool = "greeting", "get_company"
        reply = f"Olá. Sou o Funcionário Virtual da {info['name']}. Posso consultar produtos para saúde com identidade real, estoque demonstrativo, horários e reservas simuladas. Preços comerciais não estão cadastrados."
        sources = ["database:company", "treinamento/empresa.md"]
    elif any(term in lower for term in ("horário", "horario", "abre", "fecha", "funcionamento")):
        info = company(con)
        intent, tool = "opening_hours", "get_company"
        reply = info["openingHours"] + ". Os dados da empresa são demonstrativos."
        sources = ["database:company"]
    elif any(term in lower for term in ("pagamento", "pix", "cartão", "cartao")):
        info = company(con)
        intent, tool = "payments", "get_company"
        reply = info["payments"] + ". Nenhum pagamento real é processado."
        sources = ["database:company", "treinamento/pagamentos.md"]
    elif any(term in lower for term in ("entrega", "frete", "delivery")):
        info = company(con)
        intent, tool = "delivery", "get_company"
        reply = info["delivery"] + ". A operação é simulada."
        sources = ["database:company", "treinamento/entregas.md"]
    elif any(term in lower for term in ("preço", "preco", "estoque", "disponível", "disponivel", "produto", "reserv")):
        term = clean_term(message)
        result = search_products(con, term, 1, 5) if term else {"items": []}
        product = result["items"][0] if result["items"] else None
        con.execute(
            "INSERT INTO product_queries VALUES(?,?,?,?)",
            (str(uuid.uuid4()), product["id"] if product else None, term or message, now()),
        )
        tool = "search_products"
        sources = ["database:products", "database:inventory"]
        if not product:
            intent, handoff = "product_not_found", True
            reply = f"Não encontrei “{term or 'o produto informado'}” no catálogo de produtos para saúde."
        else:
            sources.append(f"anvisa:registro:{product['anvisaRegistration']}")
            if "reserv" in lower:
                quantity_match = re.search(r"\b(\d{1,3})\b", message)
                quantity = max(1, int(quantity_match.group(1)) if quantity_match else 1)
                intent = "reservation_prepare"
                reply = f"{product['name']} possui {product['quantityAvailable']} unidade(s) no estoque demonstrativo. Preparei uma reserva simulada de {quantity} unidade(s)."
                data = {"product": product, "quantity": quantity}
            elif any(term in lower for term in ("preço", "preco", "valor", "custa")):
                intent = "price_query"
                reply = f"{product['name']} é um produto real do catálogo regulatório. O preço comercial não está cadastrado neste protótipo; consulte o estabelecimento."
                data = {"product": product}
            else:
                intent = "stock_query"
                reply = f"{product['name']}: {product['quantityAvailable']} unidade(s) no estoque demonstrativo. Registro Anvisa: {product['anvisaRegistration']}."
                data = {"product": product}
    else:
        intent, tool, handoff = "unsupported", "handoff_policy", True
        reply = "Não encontrei uma fonte autorizada para responder com segurança. A solicitação foi encaminhada para atendimento humano demonstrativo."
        sources = ["treinamento/faq.md", "treinamento/politicas.md"]

    con.execute(
        "INSERT INTO conversations VALUES(?,?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            session_id,
            message,
            reply,
            intent,
            tool,
            json.dumps(sources, ensure_ascii=False),
            int(handoff),
            now(),
        ),
    )
    return {
        "message": reply,
        "intent": intent,
        "tool": tool,
        "sources": sources,
        "handoffRequired": handoff,
        "data": data,
        "identityReal": True,
        "operationsSimulated": True,
    }


def reports(con: sqlite3.Connection) -> dict:
    total_attendances = con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    reservations_count = con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    handoffs = con.execute("SELECT COUNT(*) FROM conversations WHERE handoff=1").fetchone()[0]
    out_of_stock = con.execute("SELECT COUNT(*) FROM inventory WHERE total-reserved<=0").fetchone()[0]
    top = con.execute(
        """
        SELECT p.name,COUNT(*) AS queries
        FROM product_queries q JOIN products p ON p.id=q.product_id
        GROUP BY p.id,p.name ORDER BY queries DESC,p.name LIMIT 10
        """
    ).fetchall()
    return {
        "totalAttendances": total_attendances,
        "reservations": reservations_count,
        "handoffs": handoffs,
        "outOfStockProducts": out_of_stock,
        "realIdentityProducts": con.execute("SELECT COUNT(*) FROM products WHERE identity_real=1").fetchone()[0],
        "productsWithoutPrice": con.execute("SELECT COUNT(*) FROM products WHERE price_cents IS NULL").fetchone()[0],
        "mostQueriedProducts": [dict(row) for row in top],
        "identityReal": True,
        "operationsSimulated": True,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "PredixFarmacia/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            with connect() as con:
                if path in ("/api/health", "/health"):
                    return self.send_json(
                        200,
                        {
                            "status": "ok",
                            "products": con.execute("SELECT COUNT(*) FROM products").fetchone()[0],
                            "realProducts": con.execute("SELECT COUNT(*) FROM products WHERE identity_real=1").fetchone()[0],
                            "productsWithoutPrice": con.execute("SELECT COUNT(*) FROM products WHERE price_cents IS NULL").fetchone()[0],
                            "catalogIdentity": "real",
                            "operations": "simulated",
                            "prices": "not-provided",
                            "database": "sqlite",
                            "version": "1.1.0",
                        },
                    )
                if path == "/api/company":
                    return self.send_json(200, company(con))
                if path == "/api/products":
                    query = parse_qs(parsed.query)
                    return self.send_json(
                        200,
                        search_products(
                            con,
                            query.get("query", [""])[0],
                            int(query.get("page", ["1"])[0]),
                            int(query.get("pageSize", ["24"])[0]),
                        ),
                    )
                if path == "/api/reports":
                    return self.send_json(200, reports(con))

            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (PUBLIC_DIR / relative).resolve()
            if PUBLIC_DIR.resolve() not in target.parents and target != PUBLIC_DIR.resolve():
                return self.send_json(404, {"error": "not_found"})
            if not target.is_file():
                return self.send_json(404, {"error": "not_found"})
            body = target.read_bytes()
            mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if mime.startswith("text/") or mime in ("application/javascript", "application/json"):
                mime += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self.send_json(400, {"error": str(exc), "operationsSimulated": True})

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            payload = self.read_json()
            with connect() as con:
                if path == "/api/chat":
                    return self.send_json(
                        200,
                        answer(
                            con,
                            str(payload.get("message", "")).strip(),
                            str(payload.get("sessionId", "")) or str(uuid.uuid4()),
                        ),
                    )
                if path == "/api/reservations":
                    return self.send_json(
                        201,
                        create_reservation(con, payload, self.headers.get("Idempotency-Key", "")),
                    )
                if path.startswith("/api/reservations/") and path.endswith("/cancel"):
                    return self.send_json(200, cancel_reservation(con, path.split("/")[-2]))
            return self.send_json(404, {"error": "not_found"})
        except Exception as exc:
            self.send_json(400, {"error": str(exc), "operationsSimulated": True})


if __name__ == "__main__":
    initialize()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Predix Farmácia Virtual: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
