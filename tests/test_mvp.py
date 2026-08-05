from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import app


class MVPTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        app.DB_PATH = Path(self.temp.name) / "test.db"
        app.initialize()
        self.con = app.connect()
        self.first = self.con.execute("SELECT * FROM products ORDER BY id LIMIT 1").fetchone()

    def tearDown(self) -> None:
        self.con.close()
        self.temp.cleanup()

    def test_catalog_has_exactly_500_real_products(self) -> None:
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products WHERE identity_real=1").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products WHERE anvisa_registration IS NOT NULL").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(DISTINCT sku) FROM products").fetchone()[0], 500)
        self.assertEqual(
            self.con.execute("SELECT COUNT(*) FROM (SELECT anvisa_registration,name,manufacturer FROM products GROUP BY anvisa_registration,name,manufacturer)").fetchone()[0],
            500,
        )

    def test_catalog_contains_no_synthetic_names_or_prices(self) -> None:
        synthetic = self.con.execute(
            """
            SELECT COUNT(*) FROM products
            WHERE name LIKE '%Demo %'
               OR manufacturer LIKE '%Fictícia%'
               OR manufacturer LIKE '%Simulação%'
               OR active_ingredient IS NOT NULL
            """
        ).fetchone()[0]
        self.assertEqual(synthetic, 0)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products WHERE price_cents IS NULL").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products WHERE prescription_required<>0").fetchone()[0], 0)

    def test_company_and_operations_are_explicitly_simulated(self) -> None:
        value = app.company(self.con)
        self.assertTrue(value["operationsSimulated"])
        self.assertFalse(value["identityReal"])
        self.assertIn("fictício", value["address"])

    def test_search_returns_registration_and_no_invented_price(self) -> None:
        result = app.search_products(self.con, self.first["anvisa_registration"])
        self.assertGreaterEqual(result["total"], 1)
        product = result["items"][0]
        self.assertTrue(product["identityReal"])
        self.assertTrue(product["operationsSimulated"])
        self.assertEqual(product["anvisaRegistration"], self.first["anvisa_registration"])
        self.assertIsNone(product["priceCents"])
        self.assertEqual(product["price"], "Consulte o estabelecimento")
        self.assertEqual(product["quantityAvailable"], product["quantityTotal"] - product["quantityReserved"])

    def test_product_not_found_does_not_invent(self) -> None:
        result = app.answer(self.con, "preço do Produto Absolutamente Inexistente", "session-1")
        self.assertEqual(result["intent"], "product_not_found")
        self.assertTrue(result["handoffRequired"])
        self.assertIn("Não encontrei", result["message"])

    def test_clinical_request_is_handed_off(self) -> None:
        result = app.answer(self.con, "qual remédio e dosagem devo tomar para dor?", "session-2")
        self.assertEqual(result["intent"], "clinical_handoff")
        self.assertTrue(result["handoffRequired"])
        self.assertIn("Não posso orientar", result["message"])

    def test_price_answer_has_regulatory_source_and_no_value(self) -> None:
        result = app.answer(self.con, f"preço do {self.first['anvisa_registration']}", "session-3")
        self.assertEqual(result["intent"], "price_query")
        self.assertIn("preço comercial não está cadastrado", result["message"])
        self.assertIn("database:products", result["sources"])
        self.assertIn(f"anvisa:registro:{self.first['anvisa_registration']}", result["sources"])

    def test_reservation_is_atomic_idempotent_and_price_null(self) -> None:
        product_id = int(self.first["id"])
        before = app.search_products(self.con, self.first["sku"])["items"][0]["quantityAvailable"]
        quantity = 1 if before > 0 else 0
        if quantity == 0:
            product = self.con.execute("SELECT p.* FROM products p JOIN inventory i ON i.product_id=p.id WHERE i.total>0 ORDER BY p.id LIMIT 1").fetchone()
            product_id = int(product["id"])
            before = app.search_products(self.con, product["sku"])["items"][0]["quantityAvailable"]
            sku = product["sku"]
        else:
            sku = self.first["sku"]
        payload = {"customerName": "Cliente demonstração", "items": [{"productId": product_id, "quantity": 1}]}
        first = app.create_reservation(self.con, payload, "key-001")
        second = app.create_reservation(self.con, payload, "key-001")
        self.assertEqual(first["id"], second["id"])
        self.assertIsNone(first["totalCents"])
        after = app.search_products(self.con, sku)["items"][0]["quantityAvailable"]
        self.assertEqual(after, before - 1)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0], 1)

    def test_reservation_above_stock_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Estoque insuficiente"):
            app.create_reservation(
                self.con,
                {"customerName": "Cliente", "items": [{"productId": int(self.first["id"]), "quantity": 99999}]},
                "key-over",
            )
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0], 0)

    def test_cancellation_returns_reserved_stock(self) -> None:
        product = self.con.execute("SELECT p.* FROM products p JOIN inventory i ON i.product_id=p.id WHERE i.total>0 ORDER BY p.id LIMIT 1").fetchone()
        before = app.search_products(self.con, product["sku"])["items"][0]["quantityAvailable"]
        created = app.create_reservation(
            self.con,
            {"customerName": "Cliente", "items": [{"productId": int(product["id"]), "quantity": 1}]},
            "key-cancel",
        )
        cancelled = app.cancel_reservation(self.con, created["id"])
        self.assertEqual(cancelled["status"], "CANCELLED")
        after = app.search_products(self.con, product["sku"])["items"][0]["quantityAvailable"]
        self.assertEqual(after, before)

    def test_inventory_constraints_block_negative_or_below_reserved(self) -> None:
        product = self.con.execute("SELECT p.* FROM products p JOIN inventory i ON i.product_id=p.id WHERE i.total>0 ORDER BY p.id LIMIT 1").fetchone()
        product_id = int(product["id"])
        app.create_reservation(
            self.con,
            {"customerName": "Cliente", "items": [{"productId": product_id, "quantity": 1}]},
            "key-constraint",
        )
        with self.assertRaises(Exception):
            self.con.execute("UPDATE inventory SET total=0 WHERE product_id=?", (product_id,))
        other = self.con.execute("SELECT product_id FROM inventory WHERE product_id<>? LIMIT 1", (product_id,)).fetchone()[0]
        with self.assertRaises(Exception):
            self.con.execute("UPDATE inventory SET total=-1 WHERE product_id=?", (other,))

    def test_reports_derive_real_identity_and_simulated_operations(self) -> None:
        app.answer(self.con, f"preço do {self.first['anvisa_registration']}", "session-report")
        product = self.con.execute("SELECT p.* FROM products p JOIN inventory i ON i.product_id=p.id WHERE i.total>0 ORDER BY p.id LIMIT 1").fetchone()
        app.create_reservation(
            self.con,
            {"customerName": "Cliente", "items": [{"productId": int(product["id"]), "quantity": 1}]},
            "key-report",
        )
        report = app.reports(self.con)
        self.assertEqual(report["realIdentityProducts"], 500)
        self.assertEqual(report["productsWithoutPrice"], 500)
        self.assertEqual(report["totalAttendances"], 1)
        self.assertEqual(report["reservations"], 1)
        self.assertTrue(report["mostQueriedProducts"])
        self.assertTrue(report["operationsSimulated"])

    def test_catalog_load_is_reproducible_and_initialize_idempotent(self) -> None:
        first = self.con.execute("SELECT sku,name,anvisa_registration,price_cents FROM products WHERE id=500").fetchone()
        app.initialize()
        second = self.con.execute("SELECT sku,name,anvisa_registration,price_cents FROM products WHERE id=500").fetchone()
        self.assertEqual(tuple(first), tuple(second))
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM audit WHERE action='REAL_CATALOG_LOADED'").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
