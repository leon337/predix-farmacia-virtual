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

    def tearDown(self) -> None:
        self.con.close()
        self.temp.cleanup()

    def test_seed_has_exactly_500_demo_products(self) -> None:
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products WHERE is_demo=1").fetchone()[0], 500)
        self.assertEqual(self.con.execute("SELECT COUNT(DISTINCT sku) FROM products").fetchone()[0], 500)

    def test_company_is_explicitly_fictitious(self) -> None:
        value = app.company(self.con)
        self.assertTrue(value["isDemo"])
        self.assertIn("fictício", value["address"])

    def test_search_returns_dynamic_price_and_stock(self) -> None:
        result = app.search_products(self.con, "Aurilex Demo 001")
        self.assertEqual(result["total"], 1)
        product = result["items"][0]
        self.assertGreater(product["priceCents"], 0)
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

    def test_price_answer_has_database_sources(self) -> None:
        result = app.answer(self.con, "preço do Aurilex Demo 001", "session-3")
        self.assertEqual(result["intent"], "price")
        self.assertIn("database:products", result["sources"])
        self.assertIn("database:inventory", result["sources"])

    def test_reservation_is_atomic_and_idempotent(self) -> None:
        before = app.search_products(self.con, "PFV-00001")["items"][0]["quantityAvailable"]
        payload = {"customerName": "Cliente Demo", "items": [{"productId": 1, "quantity": 2}]}
        first = app.create_reservation(self.con, payload, "key-001")
        second = app.create_reservation(self.con, payload, "key-001")
        self.assertEqual(first["id"], second["id"])
        after = app.search_products(self.con, "PFV-00001")["items"][0]["quantityAvailable"]
        self.assertEqual(after, before - 2)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0], 1)

    def test_reservation_above_stock_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Estoque insuficiente"):
            app.create_reservation(self.con, {"customerName": "Cliente", "items": [{"productId": 1, "quantity": 99999}]}, "key-over")
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0], 0)

    def test_cancellation_returns_reserved_stock(self) -> None:
        before = app.search_products(self.con, "PFV-00002")["items"][0]["quantityAvailable"]
        created = app.create_reservation(self.con, {"customerName": "Cliente", "items": [{"productId": 2, "quantity": 1}]}, "key-cancel")
        cancelled = app.cancel_reservation(self.con, created["id"])
        self.assertEqual(cancelled["status"], "CANCELLED")
        after = app.search_products(self.con, "PFV-00002")["items"][0]["quantityAvailable"]
        self.assertEqual(after, before)

    def test_inventory_constraints_block_negative_or_below_reserved(self) -> None:
        app.create_reservation(self.con, {"customerName": "Cliente", "items": [{"productId": 3, "quantity": 1}]}, "key-constraint")
        with self.assertRaises(Exception):
            self.con.execute("UPDATE inventory SET total=0 WHERE product_id=3")
        with self.assertRaises(Exception):
            self.con.execute("UPDATE inventory SET total=-1 WHERE product_id=4")

    def test_reports_are_derived_from_operations(self) -> None:
        app.answer(self.con, "preço do Aurilex Demo 001", "session-report")
        app.create_reservation(self.con, {"customerName": "Cliente", "items": [{"productId": 1, "quantity": 1}]}, "key-report")
        report = app.reports(self.con)
        self.assertEqual(report["totalAttendances"], 1)
        self.assertEqual(report["reservations"], 1)
        self.assertTrue(report["mostQueriedProducts"])

    def test_seed_is_reproducible_and_initialize_is_idempotent(self) -> None:
        first = self.con.execute("SELECT sku,name,price_cents FROM products WHERE id=500").fetchone()
        app.initialize()
        second = self.con.execute("SELECT sku,name,price_cents FROM products WHERE id=500").fetchone()
        self.assertEqual(tuple(first), tuple(second))
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM products").fetchone()[0], 500)


if __name__ == "__main__":
    unittest.main()
