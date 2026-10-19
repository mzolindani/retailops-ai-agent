
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw" / "olist"

FILES = {
    "products": "olist_products_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "product_category_name_translation": (
        "product_category_name_translation.csv"
    ),
}

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
}


def main():
    load_dotenv(ROOT / ".env")

    required = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            f"Missing database settings in .env: {', '.join(missing)}"
        )

    db_url = URL.create(
        "postgresql+psycopg",
        username=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.environ["PGDATABASE"],
    )
    engine = create_engine(db_url)

    for table, filename in FILES.items():
        path = DATA_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        print(f"Loading {filename}...")
        df = pd.read_csv(path)

        for column in DATE_COLUMNS.get(table, []):
            df[column] = pd.to_datetime(df[column], errors="coerce")

        df.to_sql(
            table,
            engine,
            if_exists="replace",
            index=False,
            chunksize=2000,
            method="multi",
        )
        print(f"Loaded {len(df):,} rows into {table}")

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_products_category "
        "ON products (product_category_name)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_product "
        "ON order_items (product_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order "
        "ON order_items (order_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status "
        "ON orders (order_status)",
    ]

    with engine.begin() as connection:
        for statement in indexes:
            connection.execute(text(statement))

    with engine.connect() as connection:
        for table in FILES:
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one()
            print(f"{table}: {count:,} rows verified")

    engine.dispose()
    print("Dataset load completed successfully.")


if __name__ == "__main__":
    main()
