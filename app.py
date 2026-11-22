import logging
import os
from contextlib import closing
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Flask, jsonify, redirect, render_template, request, url_for
print("satarting app.py")
app = Flask(__name__, static_folder=None)
logger = logging.getLogger(__name__)


def get_db_connection():
    required_settings = ("MYSQL_HOST", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD")
    missing_settings = [name for name in required_settings if not os.getenv(name)]
    if missing_settings:
        raise ValueError(
            "Missing required database settings: " + ", ".join(missing_settings)
        )

    return mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.environ["MYSQL_DATABASE"],
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        connection_timeout=5,
    )


def _fetch_products():
    with closing(get_db_connection()) as connection:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(
                """
                SELECT id, name, description, price, stock_quantity
                FROM products
                ORDER BY id
                """
            )
            products = cursor.fetchall()

    return [
        {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "price": str(product["price"]) if product["price"] is not None else None,
            "stock_quantity": product["stock_quantity"],
        }
        for product in products
    ]


def _render_products_page(error=None, added=False, form_values=None, status=200):
    try:
        products = _fetch_products()
    except (mysql.connector.Error, ValueError):
        logger.exception("Unable to retrieve products from MySQL")
        return (
            render_template(
                "products.html",
                products=[],
                error="Database unavailable",
                added=False,
                form_values=form_values or {},
            ),
            503,
        )

    return (
        render_template(
            "products.html",
            products=products,
            error=error,
            added=added,
            form_values=form_values or {},
        ),
        status,
    )


@app.get("/")
def products_page():
    return _render_products_page(added=request.args.get("added") == "1")


@app.post("/products")
def create_product():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    price_text = request.form.get("price", "").strip()
    stock_text = request.form.get("stock_quantity", "").strip()
    form_values = {
        "name": name,
        "description": description or "",
        "price": price_text,
        "stock_quantity": stock_text,
    }

    if not name or len(name) > 255:
        return _render_products_page(
            error="Enter a name of 1 to 255 characters.",
            form_values=form_values,
            status=400,
        )

    try:
        price = Decimal(price_text)
        if (
            not price.is_finite()
            or price < 0
            or price > Decimal("99999999.99")
            or price.as_tuple().exponent < -2
        ):
            raise ValueError("Invalid price")
    except (InvalidOperation, ValueError):
        return _render_products_page(
            error="Enter a price from 0 to 99999999.99 with up to 2 decimal places.",
            form_values=form_values,
            status=400,
        )

    try:
        stock_quantity = int(stock_text)
        if stock_quantity < 0 or stock_quantity > 4294967295:
            raise ValueError("Invalid stock quantity")
    except ValueError:
        return _render_products_page(
            error="Enter a whole-number stock quantity from 0 to 4294967295.",
            form_values=form_values,
            status=400,
        )

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO products (name, description, price, stock_quantity)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (name, description, price, stock_quantity),
                )
            connection.commit()
    except (mysql.connector.Error, ValueError):
        logger.exception("Unable to add product to MySQL")
        return (
            render_template(
                "products.html",
                products=[],
                error="Unable to save product; database unavailable.",
                added=False,
                form_values=form_values,
            ),
            503,
        )

    return redirect(url_for("products_page", added=1), code=303)


@app.get("/api/products")
def list_products():
    try:
        products = _fetch_products()
    except (mysql.connector.Error, ValueError):
        logger.exception("Unable to retrieve products from MySQL")
        return jsonify({"error": "Database unavailable"}), 503

    return jsonify(products)
print("ending app.py")