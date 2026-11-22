import unittest
from decimal import Decimal
from unittest.mock import patch

import mysql.connector

from app import app


class ProductsEndpointTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("app.get_db_connection")
    def test_returns_all_products_as_json(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Travel mug",
                "description": "Insulated mug",
                "price": Decimal("18.00"),
                "stock_quantity": 0,
            }
        ]

        response = self.client.get("/api/products")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            [
                {
                    "id": 1,
                    "name": "Travel mug",
                    "description": "Insulated mug",
                    "price": "18.00",
                    "stock_quantity": 0,
                }
            ],
        )
        cursor.execute.assert_called_once()

    @patch("app.get_db_connection")
    def test_returns_empty_array_when_no_products_exist(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchall.return_value = []

        response = self.client.get("/api/products")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    @patch("app.get_db_connection")
    def test_homepage_displays_products_as_html(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "<Travel mug>",
                "description": "Insulated mug",
                "price": Decimal("18.00"),
                "stock_quantity": 0,
            }
        ]

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        self.assertIn(b"&lt;Travel mug&gt;", response.data)
        self.assertIn(b"<table>", response.data)
        self.assertIn(b"18.00", response.data)
        self.assertIn(b"Add a product", response.data)

    @patch("app.get_db_connection")
    def test_adds_product_from_form(self, get_connection):
        response = self.client.post(
            "/products",
            data={
                "name": "New product",
                "description": "A test product",
                "price": "12.50",
                "stock_quantity": "4",
            },
        )

        cursor = get_connection.return_value.cursor.return_value
        self.assertEqual(response.status_code, 303)
        self.assertIn("/?added=1", response.headers["Location"])
        cursor.execute.assert_called_once()
        self.assertEqual(
            cursor.execute.call_args.args[1],
            ("New product", "A test product", Decimal("12.50"), 4),
        )
        get_connection.return_value.commit.assert_called_once()

    @patch("app.get_db_connection")
    def test_rejects_negative_stock_quantity(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchall.return_value = []

        response = self.client.post(
            "/products",
            data={
                "name": "New product",
                "description": "",
                "price": "12.50",
                "stock_quantity": "-1",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"whole-number stock quantity", response.data)
        get_connection.return_value.commit.assert_not_called()
        cursor.execute.assert_called_once()

    @patch("app.get_db_connection", side_effect=mysql.connector.Error("offline"))
    def test_returns_service_unavailable_when_database_fails(self, _get_connection):
        response = self.client.get("/api/products")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "Database unavailable"})


if __name__ == "__main__":
    unittest.main()
