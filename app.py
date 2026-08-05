from __future__ import annotations

import json
import os
import random
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PREDIX_DATABASE_PATH", ROOT / "data" / "predix.db"))
ADMIN_KEY = os.environ.get("PREDIX_ADMIN_KEY", "")
UTC = timezone.utc

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS company(id TEXT PRIMARY KEY,name TEXT,address TEXT,phone TEXT,opening_hours TEXT,payments TEXT,delivery TEXT,is_demo INTEGER CHECK(is_demo=1));
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,sku TEXT UNIQUE,name TEXT UNIQUE,category TEXT,manufacturer TEXT,active_ingredient TEXT,presentation TEXT,price_cents INTEGER CHECK(price_cents>0),prescription_required INTEGER,is_demo INTEGER CHECK(is_demo=1));
CREATE TABLE IF NOT EXISTS inventory(product_id INTEGER PRIMARY KEY REFERENCES products(id),total INTEGER CHECK(total>=0),reserved INTEGER DEFAULT 0 CHECK(reserved>=0),minimum INTEGER DEFAULT 5,updated_at TEXT,CHECK(reserved<=total));
CREATE TABLE IF NOT EXISTS customers(id TEXT PRIMARY KEY,name TEXT,contact TEXT,is_demo INTEGER CHECK(is_demo=1),created_at TEXT);
CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY,customer_id TEXT REFERENCES customers(id),status TEXT,expires_at TEXT,idempotency_key TEXT UNIQUE,created_at TEXT,cancelled_at TEXT);
CREATE TABLE IF NOT EXISTS reservation_items(reservation_id TEXT REFERENCES reservations(id),product_id INTEGER REFERENCES products(id),quantity INTEGER CHECK(quantity>0),price_cents INTEGER,PRIMARY KEY(reservation_id,product_id));
CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,session_id TEXT,user_message TEXT,assistant_message TEXT,intent TEXT,tool TEXT,sources TEXT,handoff INTEGER,created_at TEXT);
CREATE TABLE IF NOT EXISTS product_queries(id TEXT PRIMARY KEY,product_id INTEGER,query_text TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,actor TEXT,action TEXT,resource TEXT,before_json TEXT,after_json TEXT,created_at TEXT);
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


def initialize() -> None:
    with connect() as con:
        con.executescript(SCHEMA)
        if con.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
            return
        stamp = now()
        con.execute(
            "INSERT INTO company VALUES(?,?,?,?,?,?,?,1)",
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
        categories = ["Analgésicos demo", "Higiene", "Dermocosméticos", "Vitaminas demo", "Infantil", "Primeiros socorros", "Respiratórios", "Saúde bucal", "Bem-estar", "Acessórios"]
        prefixes = ["Auri", "Bene", "Cali", "Dermo", "Evo", "Farma", "Gena", "Higi", "Íris", "Juno", "Kira", "Lumi", "Medi", "Nexa", "Onda", "Pura", "Quori", "Riva", "Sani", "Vita"]
        suffixes = ["lex", "care", "plus", "vida", "soft"]
        makers = ["Aurora Demo", "Horizonte Fictícia", "Predix Labs Simulação", "Saúde Modelo Demo", "Farma Exemplo Fictícia"]
        forms = ["caixa com 10 unidades", "caixa com 20 unidades", "frasco de 100 mL", "frasco de 200 mL", "bisnaga de 30 g"]
        rng = random.Random(337)
        con.execute("BEGIN IMMEDIATE")
        try:
            for i in range(1, 501):
                name = f"{prefixes[(i-1)%20]}{suffixes[((i-1)//20)%5]} Demo {i:03d}"
                con.execute(
                    "INSERT INTO products(sku,name,category,manufacturer,active_ingredient,presentation,price_cents,prescription_required,is_demo) VALUES(?,?,?,?,?,?,?,?,1)",
                    (f"PFV-{i:05d}", name, categories[(i-1)%10], makers[(i-1)%5], f"Composto demonstrativo {(i-1)%7+1}", forms[(i-1)%5], 350 + (i*137)%28000, int(i%7==0)),
                )
                total = 0 if i % 17 == 0 else rng.randint(4, 120)
                con.execute("INSERT INTO inventory VALUES(?,?,?,?,?)", (i, total, 0, rng.randint(3, 12), stamp))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise


def company(con: sqlite3.Connection) -> dict:
    row = con.execute("SELECT * FROM company LIMIT 1").fetchone()
    return {"id": row["id"], "name": row["name"], "address": row["address"], "phone": row["phone"], "openingHours": row["opening_hours"], "payments": row["payments"], "delivery": row["delivery"], "isDemo": True}


def product_dict(row: sqlite3.Row) -> dict:
    available = row["total"] - row["reserved"]
    return {"id": row["id"], "sku": row["sku"], "name": row["name"], "category": row["category"], "manufacturer": row["manufacturer"], "activeIngredient": row["active_ingredient"], "presentation": row["presentation"], "priceCents": row["price_cents"], "price": f"R$ {row['price_cents']/100:.2f}".replace(".", ","), "quantityTotal": row["total"], "quantityReserved": row["reserved"], "quantityAvailable": available, "minimum": row["minimum"], "prescriptionRequired": bool(row["prescription_required"]), "isDemo": True}


def search_products(con: sqlite3.Connection, query: str = "", page: int = 1, page_size: int = 24) -> dict:
    page, page_size = max(1, page), min(100, max(1, page_size))
    base = "FROM products p JOIN inventory i ON i.product_id=p.id"
    params: list[object] = []
    where = ""
    if query.strip():
        where = " WHERE p.name LIKE ? COLLATE NOCASE OR p.sku LIKE ? COLLATE NOCASE OR p.category LIKE ? COLLATE NOCASE OR p.manufacturer LIKE ? COLLATE NOCASE OR p.active_ingredient LIKE ? COLLATE NOCASE"
        term = f"%{query.strip()}%"
        params = [term] * 5
    total = con.execute("SELECT COUNT(*) " + base + where, params).fetchone()[0]
    rows = con.execute("SELECT p.*,i.total,i.reserved,i.minimum " + base + where + " ORDER BY p.name LIMIT ? OFFSET ?", [*params, page_size, (page-1)*page_size]).fetchall()
    return {"items": [product_dict(r) for r in rows], "page": page, "pageSize": page_size, "total": total, "totalPages": (total+page_size-1)//page_size, "isDemo": True}


def reservation(con: sqlite3.Connection, reservation_id: str) -> dict:
    row = con.execute("SELECT r.*,c.name,c.contact FROM reservations r JOIN customers c ON c.id=r.customer_id WHERE r.id=?", (reservation_id,)).fetchone()
    if not row:
        raise ValueError("Reserva não encontrada.")
    items = con.execute("SELECT ri.product_id,p.name,ri.quantity,ri.price_cents FROM reservation_items ri JOIN products p ON p.id=ri.product_id WHERE ri.reservation_id=?", (reservation_id,)).fetchall()
    return {"id": row["id"], "customer": row["name"], "status": row["status"], "expiresAt": row["expires_at"], "createdAt": row["created_at"], "items": [dict(i) for i in items], "totalCents": sum(i["quantity"]*i["price_cents"] for i in items), "isDemo": True}


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
            pid, qty = int(item["productId"]), int(item["quantity"])
            if qty <= 0:
                raise ValueError("Quantidade inválida.")
            row = con.execute("SELECT p.name,p.price_cents,i.total,i.reserved FROM products p JOIN inventory i ON i.product_id=p.id WHERE p.id=?", (pid,)).fetchone()
            if not row:
                raise ValueError(f"Produto {pid} não encontrado.")
            if qty > row["total"] - row["reserved"]:
                raise ValueError(f"Estoque insuficiente para {row['name']}.")
            selected.append((pid, qty, row))
        con.execute("INSERT INTO customers VALUES(?,?,?,?,?)", (cid, name, str(payload.get("contact", "")) or None, 1, stamp))
        con.execute("INSERT INTO reservations(id,customer_id,status,expires_at,idempotency_key,created_at) VALUES(?,?,'ACTIVE',?,?,?)", (rid, cid, expires, key, stamp))
        for pid, qty, row in selected:
            con.execute("INSERT INTO reservation_items VALUES(?,?,?,?)", (rid, pid, qty, row["price_cents"]))
            con.execute("UPDATE inventory SET reserved=reserved+?,updated_at=? WHERE product_id=?", (qty, stamp, pid))
        con.execute("INSERT INTO audit VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), "virtual-employee", "RESERVATION_CREATED", rid, None, json.dumps(payload, ensure_ascii=False), stamp))
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return reservation(con, rid)


def cancel_reservation(con: sqlite3.Connection, rid: str) -> dict:
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT status FROM reservations WHERE id=?", (rid,)).fetchone()
        if not row:
            raise ValueError("Reserva não encontrada.")
        if row["status"] == "ACTIVE":
            for item in con.execute("SELECT product_id,quantity FROM reservation_items WHERE reservation_id=?", (rid,)).fetchall():
                con.execute("UPDATE inventory SET reserved=reserved-?,updated_at=? WHERE product_id=?", (item["quantity"], now(), item["product_id"]))
            con.execute("UPDATE reservations SET status='CANCELLED',cancelled_at=? WHERE id=?", (now(), rid))
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return reservation(con, rid)


def clean_term(message: str) -> str:
    text = re.sub(r"\b(qual|quanto|custa|preço|preco|valor|tem|estoque|disponível|disponivel|produto|buscar|procure|reservar|reserve|reserva|unidade|unidades|por|favor|do|da|de|o|a|os|as|em)\b", " ", message, flags=re.I)
    tokens = re.sub(r"[^\wÀ-ÿ-]+", " ", text).split()
    if len(tokens) > 1 and tokens[0].isdigit():
        tokens = tokens[1:]
    return " ".join(tokens)


def answer(con: sqlite3.Connection, message: str, session_id: str) -> dict:
    lower = message.casefold()
    sources: list[str] = []
    tool, handoff, data = None, False, {}
    clinical = ("dose", "dosagem", "posologia", "diagnóstico", "diagnostico", "sintoma", "tratamento", "o que devo tomar", "qual remédio", "qual remedio")
    if any(x in lower for x in clinical):
        intent, tool, handoff = "clinical_handoff", "safety_policy", True
        reply = "Não posso orientar diagnóstico, tratamento, dosagem ou uso de medicamentos. Este ambiente fictício encaminharia a solicitação a um farmacêutico ou profissional de saúde humano."
        sources = ["treinamento/politicas.md"]
    elif any(x in lower for x in ("olá", "ola", "oi", "bom dia", "boa tarde", "boa noite")):
        c = company(con); intent, tool = "greeting", "get_company"
        reply = f"Olá. Sou o Funcionário Virtual da {c['name']}. Posso consultar produtos, preços, estoque, horários e reservas simuladas."
        sources = ["database:company", "treinamento/empresa.md"]
    elif any(x in lower for x in ("horário", "horario", "abre", "fecha", "funcionamento")):
        c = company(con); intent, tool = "opening_hours", "get_company"; reply = c["openingHours"] + ". Dados fictícios."; sources = ["database:company"]
    elif any(x in lower for x in ("pagamento", "pix", "cartão", "cartao")):
        c = company(con); intent, tool = "payments", "get_company"; reply = c["payments"] + ". Nenhum pagamento real é processado."; sources = ["database:company", "treinamento/pagamentos.md"]
    elif any(x in lower for x in ("entrega", "frete", "delivery")):
        c = company(con); intent, tool = "delivery", "get_company"; reply = c["delivery"] + "."; sources = ["database:company", "treinamento/entregas.md"]
    elif any(x in lower for x in ("preço", "preco", "estoque", "disponível", "disponivel", "produto", "reserv")):
        term = clean_term(message)
        result = search_products(con, term, 1, 5) if term else {"items": []}
        product = result["items"][0] if result["items"] else None
        con.execute("INSERT INTO product_queries VALUES(?,?,?,?)", (str(uuid.uuid4()), product["id"] if product else None, term, now()))
        tool = "search_products"; sources = ["database:products", "database:inventory"]
        if not product:
            intent, handoff = "product_not_found", True
            reply = f"Não encontrei “{term or 'o produto informado'}” no catálogo fictício."
        elif "reserv" in lower:
            qty_match = re.search(r"\b(\d{1,3})\b", message); qty = int(qty_match.group(1)) if qty_match else 1
            intent = "reservation_ready"
            reply = f"Encontrei {product['name']}. Há {product['quantityAvailable']} unidade(s); use o formulário para reservar {qty} unidade(s)."
            data = {"product": product, "quantity": qty}
        elif any(x in lower for x in ("preço", "preco", "valor", "custa")):
            intent = "price"; reply = f"{product['name']} custa {product['price']} no ambiente fictício."; data = {"product": product}
        else:
            intent = "stock"; reply = f"{product['name']} possui {product['quantityAvailable']} unidade(s) disponíveis na simulação."; data = {"product": product}
    else:
        intent, tool, handoff = "unknown", "knowledge_lookup", True
        reply = "Não localizei fonte confiável para responder. A solicitação foi marcada para atendimento humano fictício."
    cid = str(uuid.uuid4())
    con.execute("INSERT INTO conversations VALUES(?,?,?,?,?,?,?,?,?)", (cid, session_id, message, reply, intent, tool, json.dumps(sources), int(handoff), now()))
    return {"message": reply, "intent": intent, "tool": tool, "sources": sources, "handoffRequired": handoff, "data": data, "sessionId": session_id, "conversationId": cid, "isDemo": True}


def reports(con: sqlite3.Connection) -> dict:
    attend = con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    handoffs = con.execute("SELECT COUNT(*) FROM conversations WHERE handoff=1").fetchone()[0]
    reservations = con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    out = con.execute("SELECT COUNT(*) FROM inventory WHERE total-reserved=0").fetchone()[0]
    top = con.execute("SELECT p.name,COUNT(q.id) queries FROM product_queries q JOIN products p ON p.id=q.product_id GROUP BY p.id ORDER BY queries DESC LIMIT 10").fetchall()
    return {"totalAttendances": attend, "handoffs": handoffs, "reservations": reservations, "outOfStockProducts": out, "mostQueriedProducts": [dict(r) for r in top], "isDemo": True}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

    def read_json(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        if size < 1 or size > 1_000_000:
            raise ValueError("Corpo JSON ausente ou grande demais.")
        value = json.loads(self.rfile.read(size))
        if not isinstance(value, dict):
            raise ValueError("O corpo deve ser um objeto JSON.")
        return value

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path); path = parsed.path; query = parse_qs(parsed.query)
            with connect() as con:
                if path == "/api/health": return self.send_json(200, {"status": "ok", "products": con.execute("SELECT COUNT(*) FROM products").fetchone()[0], "isDemo": True})
                if path == "/api/company": return self.send_json(200, company(con))
                if path == "/api/products": return self.send_json(200, search_products(con, query.get("query", [""])[0], int(query.get("page", ["1"])[0]), int(query.get("pageSize", ["24"])[0])))
                if path == "/api/reports": return self.send_json(200, reports(con))
                if path.startswith("/api/reservations/"): return self.send_json(200, reservation(con, path.rsplit("/", 1)[1]))
            target = ROOT / ("index.html" if path == "/" else path.lstrip("/"))
            if target.resolve().parent != ROOT.resolve() or not target.is_file(): return self.send_json(404, {"error": "not_found"})
            body = target.read_bytes(); mime = "text/html; charset=utf-8" if target.suffix == ".html" else "text/plain; charset=utf-8"
            self.send_response(200); self.send_header("Content-Type", mime); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        except Exception as exc:
            self.send_json(400, {"error": str(exc), "isDemo": True})

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path; payload = self.read_json()
            with connect() as con:
                if path == "/api/chat": return self.send_json(200, answer(con, str(payload.get("message", "")).strip(), str(payload.get("sessionId", "")) or str(uuid.uuid4())))
                if path == "/api/reservations": return self.send_json(201, create_reservation(con, payload, self.headers.get("Idempotency-Key", "")))
                if path.startswith("/api/reservations/") and path.endswith("/cancel"): return self.send_json(200, cancel_reservation(con, path.split("/")[-2]))
                if path.startswith("/api/admin/inventory/"):
                    if not ADMIN_KEY or self.headers.get("X-Admin-Key") != ADMIN_KEY: return self.send_json(401, {"error": "unauthorized"})
                    pid, total = int(path.rsplit("/", 1)[1]), int(payload["quantityTotal"])
                    row = con.execute("SELECT total,reserved FROM inventory WHERE product_id=?", (pid,)).fetchone()
                    if not row or total < row["reserved"] or total < 0: raise ValueError("Quantidade inválida.")
                    con.execute("UPDATE inventory SET total=?,updated_at=? WHERE product_id=?", (total, now(), pid)); con.execute("INSERT INTO audit VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), "admin", "INVENTORY_UPDATED", str(pid), json.dumps(dict(row)), json.dumps({"total": total}), now()))
                    return self.send_json(200, search_products(con, f"PFV-{pid:05d}", 1, 1)["items"][0])
            return self.send_json(404, {"error": "not_found"})
        except Exception as exc:
            self.send_json(400, {"error": str(exc), "isDemo": True})


if __name__ == "__main__":
    initialize()
    host, port = os.environ.get("HOST", "127.0.0.1"), int(os.environ.get("PORT", "8000"))
    print(f"Predix Farmácia Virtual: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
