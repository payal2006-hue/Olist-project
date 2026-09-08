import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw"


# ============================================================
# DATASETS
# ============================================================

DATASETS = {
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
}


# ============================================================
# DATE COLUMNS
# ============================================================

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],

    "order_items": [
        "shipping_limit_date",
    ],

    "reviews": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}


# ============================================================
# LOAD + TRANSFORM
# ============================================================

def load_csv(table_name, filename):
    """Read a CSV file into a pandas DataFrame."""

    file_path = DATA_PATH / filename

    print(f"\nReading: {filename}")

    df = pd.read_csv(file_path)

    print(f"Rows loaded: {len(df):,}")

    return df


def transform_data(table_name, df):
    """Apply table-specific transformations."""

    # Convert date columns
    if table_name in DATE_COLUMNS:

        for column in DATE_COLUMNS[table_name]:

            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

    return df


def load_to_postgres(table_name, df):
    """Load DataFrame into PostgreSQL."""

    print(f"Loading {table_name}...")

    df.to_sql(
    table_name,
    engine,
    if_exists="append",
    index=False,
    method="multi",
    chunksize=1000
)

    print(
        f"Successfully loaded "
        f"{len(df):,} rows into {table_name}"
    )


# ============================================================
# MAIN ETL PIPELINE
# ============================================================

def main():

    print("=" * 60)
    print("OLIST ETL PIPELINE")
    print("=" * 60)

    # Only load the tables that failed previously
    tables_to_load = {
        "payments": DATASETS["payments"],
        "reviews": DATASETS["reviews"],
    }

    for table_name, filename in tables_to_load.items():

        try:

            # Extract
            df = load_csv(
                table_name,
                filename
            )

            # Transform
            df = transform_data(
                table_name,
                df
            )

            # Load
            load_to_postgres(
                table_name,
                df
            )

        except Exception as e:

            print(
                f"\nERROR loading {table_name}:"
            )

            print(e)

            raise

    print("\n" + "=" * 60)
    print("ETL PIPELINE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()