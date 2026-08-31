"""
load_data.py
Loads the raw Olist CSV files into the PostgreSQL `olist_db` database.

Usage:
    python src/load_data.py

Assumes:
    - sql/01_schema.sql has already been run to create empty tables
    - CSVs live in data/raw/
"""

import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

DB_URI = "postgresql+psycopg2://olist_user:olist_pass@localhost:5432/olist_db"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

engine = create_engine(DB_URI)

# Order matters: parents before children (FK constraints)
TABLES = [
    {
        "csv": "product_category_name_translation.csv",
        "table": "category_translation",
        "parse_dates": [],
        "encoding": "utf-8-sig",  # file has a BOM
    },
    {
        "csv": "olist_customers_dataset.csv",
        "table": "customers",
        "parse_dates": [],
    },
    {
        "csv": "olist_sellers_dataset.csv",
        "table": "sellers",
        "parse_dates": [],
    },
    {
        "csv": "olist_products_dataset.csv",
        "table": "products",
        "parse_dates": [],
        "rename": {
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        },
    },
    {
        "csv": "olist_orders_dataset.csv",
        "table": "orders",
        "parse_dates": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    {
        "csv": "olist_order_items_dataset.csv",
        "table": "order_items",
        "parse_dates": ["shipping_limit_date"],
    },
    {
        "csv": "olist_order_payments_dataset.csv",
        "table": "order_payments",
        "parse_dates": [],
    },
    {
        "csv": "olist_order_reviews_dataset.csv",
        "table": "order_reviews",
        "parse_dates": ["review_creation_date", "review_answer_timestamp"],
    },
]


def load_table(spec: dict) -> None:
    path = RAW_DIR / spec["csv"]
    print(f"Loading {spec['csv']} -> {spec['table']} ...")

    df = pd.read_csv(
        path,
        encoding=spec.get("encoding", "utf-8"),
        parse_dates=spec["parse_dates"] if spec["parse_dates"] else None,
    )

    if "rename" in spec:
        df = df.rename(columns=spec["rename"])

    # products.category can have NaN category names; category_translation
    # table has no row for those, so leaving them NULL is correct (nullable FK).
    if spec["table"] == "products":
        df["product_category_name"] = df["product_category_name"].where(
            df["product_category_name"].notna(), None
        )

    # Some Olist reviews have duplicate (review_id, order_id) pairs from data
    # quality issues upstream; drop exact duplicates to respect our PK.
    if spec["table"] == "order_reviews":
        before = len(df)
        df = df.drop_duplicates(subset=["review_id", "order_id"])
        dropped = before - len(df)
        if dropped:
            print(f"  dropped {dropped} duplicate review rows")

    df.to_sql(spec["table"], engine, if_exists="append", index=False, method="multi", chunksize=5000)
    print(f"  loaded {len(df):,} rows")


def main():
    for spec in TABLES:
        load_table(spec)
    print("\nAll tables loaded.")


if __name__ == "__main__":
    main()
