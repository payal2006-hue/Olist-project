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
# 5. FIND REVIEWS CSV
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REVIEWS_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "raw",
    "olist_order_reviews_dataset.csv"
)


# ============================================================
# 6. READ REVIEWS CSV
# ============================================================

print("\nReading reviews CSV...")

reviews = pd.read_csv(REVIEWS_FILE)

print(
    f"Reviews CSV loaded: "
    f"{len(reviews):,} rows"
)


# ============================================================
# 7. CONVERT DATE COLUMNS
# ============================================================

date_columns = [
    "review_creation_date",
    "review_answer_timestamp"
]

for column in date_columns:

    reviews[column] = pd.to_datetime(
        reviews[column],
        errors="coerce"
    )


# ============================================================
# 8. REMOVE DUPLICATES FROM CSV
# ============================================================

before = len(reviews)

reviews = reviews.drop_duplicates(
    subset=["review_id"]
)

after = len(reviews)

print(
    f"\nDuplicate review IDs removed: "
    f"{before - after:,}"
)

print(
    f"Rows to load: "
    f"{after:,}"
)


# ============================================================
# 9. VALIDATE REVIEW IDs
# ============================================================

duplicate_ids = reviews[
    reviews["review_id"].duplicated(keep=False)
]

if len(duplicate_ids) > 0:

    print(
        "\n❌ Duplicate review IDs still exist."
    )

    print(
        duplicate_ids[
            ["review_id", "order_id"]
        ].head(20)
    )

    raise ValueError(
        "Duplicate review_id values found."
    )

else:

    print(
        "✓ All review_id values are unique."
    )


# ============================================================
# 10. CLEAR EXISTING REVIEWS
# ============================================================

print("\nClearing existing reviews table...")

with engine.begin() as connection:

    connection.execute(
        text("TRUNCATE TABLE reviews;")
    )

print("✓ Reviews table cleared.")


# ============================================================
# 11. LOAD REVIEWS IN CHUNKS
# ============================================================

print("\nLoading reviews into PostgreSQL...")

chunk_size = 1000

total_loaded = 0

try:

    for start in range(
        0,
        len(reviews),
        chunk_size
    ):

        end = min(
            start + chunk_size,
            len(reviews)
        )

        chunk = reviews.iloc[start:end]

        # Each chunk gets its own transaction
        with engine.begin() as connection:

            chunk.to_sql(
                "reviews",
                connection,
                if_exists="append",
                index=False
            )

        total_loaded += len(chunk)

        print(
            f"Loaded {total_loaded:,} / "
            f"{len(reviews):,} rows"
        )


    print(
        f"\n✅ Successfully loaded "
        f"{total_loaded:,} reviews."
    )


except Exception as e:

    print("\n❌ ERROR loading reviews")
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
# 12. VERIFY DATABASE
# ============================================================

print("\nVerifying reviews table...")

with engine.connect() as connection:

    result = connection.execute(
        text("SELECT COUNT(*) FROM reviews;")
    )

    count = result.scalar()


# ============================================================
# 13. FINAL RESULT
# ============================================================

print("\n========================================")
print("REVIEWS ETL RESULT")
print("========================================")

print(
    f"CSV rows:        {len(reviews):,}"
)

print(
    f"Rows loaded:     {total_loaded:,}"
)

print(
    f"PostgreSQL rows: {count:,}"
)

print("========================================")


if count == len(reviews):

    print(
        "\n🎉 SUCCESS!"
    )

    print(
        "All reviews were loaded successfully."
    )

else:

    print(
        "\n⚠️ WARNING!"
    )

    print(
        "The PostgreSQL count does not match "
        "the CSV count."
    )