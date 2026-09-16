import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# ============================================================
# 2. CHECK DATABASE CONFIGURATION
# ============================================================

print("Checking database configuration...")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError(
        "Database configuration is incomplete. "
        "Please check your .env file."
    )

print("Database configuration found.")


# ============================================================
# 3. CREATE DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

print("PostgreSQL engine created.")


# ============================================================
# 4. CHECK DATABASE CONNECTION
# ============================================================

with engine.connect() as connection:

    result = connection.execute(
        text("SELECT current_database(), current_user;")
    )

    print("\nPython is connected to:")
    print(result.fetchone())


# ============================================================
# 5. SET PROJECT DIRECTORY
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# 6. PAYMENTS CSV PATH
# ============================================================

PAYMENTS_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "raw",
    "olist_order_payments_dataset.csv"
)


# ============================================================
# 7. READ PAYMENTS CSV
# ============================================================

print("\nReading payments CSV...")

payments = pd.read_csv(PAYMENTS_FILE)

print(
    f"Payments CSV loaded: "
    f"{len(payments):,} rows"
)


# ============================================================
# 8. DISPLAY COLUMNS
# ============================================================

print("\nPayments columns:")

for column in payments.columns:
    print(f"  - {column}")


# ============================================================
# 9. BASIC VALIDATION
# ============================================================

print("\nBasic validation:")

print(
    "Rows:",
    f"{len(payments):,}"
)

print(
    "Columns:",
    len(payments.columns)
)

print("\nMissing values:")

print(
    payments.isnull().sum()
)


# ============================================================
# 10. CHECK PAYMENT KEYS
# ============================================================

unique_keys = (
    payments[
        ["order_id", "payment_sequential"]
    ]
    .drop_duplicates()
    .shape[0]
)

duplicate_keys = (
    payments[
        ["order_id", "payment_sequential"]
    ]
    .duplicated()
    .sum()
)

print("\nPayment key validation:")

print(
    "Total rows:",
    f"{len(payments):,}"
)

print(
    "Unique payment keys:",
    f"{unique_keys:,}"
)

print(
    "Duplicate payment keys:",
    f"{duplicate_keys:,}"
)


# ============================================================
# 11. VALIDATE PAYMENT VALUES
# ============================================================

negative_values = (
    payments["payment_value"] < 0
).sum()

invalid_installments = (
    payments["payment_installments"] < 0
).sum()

print("\nPayment value validation:")

print(
    "Negative payment values:",
    negative_values
)

print(
    "Invalid installments:",
    invalid_installments
)


# ============================================================
# 12. CLEAR EXISTING PAYMENTS TABLE
# ============================================================

print("\nClearing existing payments table...")

try:

    with engine.begin() as connection:

        connection.execute(
            text("TRUNCATE TABLE payments;")
        )

    print("✓ Payments table cleared.")

except Exception as e:

    print(
        "\n❌ Could not clear payments table."
    )

    print("Error:")
    print(e)

    raise


# ============================================================
# 13. LOAD PAYMENTS INTO POSTGRESQL
# ============================================================

print("\nLoading payments into PostgreSQL...")

chunk_size = 1000

total_loaded = 0

try:

    for start in range(
        0,
        len(payments),
        chunk_size
    ):

        end = min(
            start + chunk_size,
            len(payments)
        )

        chunk = payments.iloc[start:end]

        with engine.begin() as connection:

            chunk.to_sql(
                "payments",
                connection,
                if_exists="append",
                index=False
            )

        total_loaded += len(chunk)

        print(
            f"Loaded "
            f"{total_loaded:,} / "
            f"{len(payments):,} rows"
        )

    print(
        f"\n✅ Successfully loaded "
        f"{total_loaded:,} payments."
    )


except Exception as e:

    print("\n❌ ERROR loading payments")
    print("----------------------------------------")

    print(
        "Exception type:",
        type(e).__name__
    )

    print("\nError:")
    print(e)

    if hasattr(e, "orig"):

        print("\nPostgreSQL error:")
        print(e.orig)

    print("----------------------------------------")

    raise


# ============================================================
# 14. VERIFY DATABASE ROW COUNT
# ============================================================

print("\nVerifying payments table...")

try:

    with engine.connect() as connection:

        result = connection.execute(
            text(
                "SELECT COUNT(*) FROM payments;"
            )
        )

        database_count = result.scalar()

except Exception as e:

    print(
        "\n❌ Could not verify payments table."
    )

    print("Error:")
    print(e)

    raise


# ============================================================
# 15. VERIFY PAYMENT KEYS IN DATABASE
# ============================================================

with engine.connect() as connection:

    result = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    order_id,
                    payment_sequential
                FROM payments
                GROUP BY
                    order_id,
                    payment_sequential
            ) AS unique_payments;
            """
        )
    )

    database_unique_keys = result.scalar()


# ============================================================
# 16. FINAL RESULT
# ============================================================

print("\n========================================")
print("PAYMENTS ETL RESULT")
print("========================================")

print(
    f"CSV rows:              {len(payments):,}"
)

print(
    f"Unique CSV keys:       {unique_keys:,}"
)

print(
    f"Rows loaded:           {total_loaded:,}"
)

print(
    f"PostgreSQL rows:       {database_count:,}"
)

print(
    f"PostgreSQL unique keys:{database_unique_keys:,}"
)

print("========================================")


if (
    database_count == len(payments)
    and database_unique_keys == unique_keys
):

    print("\n🎉 SUCCESS!")

    print(
        "All payment records were loaded "
        "successfully."
    )

else:

    print("\n⚠️ WARNING!")

    print(
        "The PostgreSQL data does not "
        "match the CSV."
    )

    print(
        f"Expected rows: {len(payments):,}"
    )

    print(
        f"Found rows:    {database_count:,}"
    )