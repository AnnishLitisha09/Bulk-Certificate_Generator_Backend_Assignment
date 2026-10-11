"""
Database initialization script for Bulk Certificate Generator.
Ensures MySQL database existence and creates all SQLAlchemy relational tables.
"""

import sys
from urllib.parse import urlparse
import pymysql

from app.config import get_settings
from app.database import Base, engine, init_db
# Import models so SQLAlchemy registers tables in Base.metadata
import app.models


def setup_database():
    """Ensure database exists and create tables."""
    settings = get_settings()
    db_url = settings.DATABASE_URL
    print(f"Connecting to database configured at: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    # If using MySQL, ensure the schema exists first
    if "mysql" in db_url:
        try:
            parsed = urlparse(db_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            user = parsed.username or "root"
            password = parsed.password or ""
            db_name = parsed.path.lstrip("/").split("?")[0]

            print(f"Checking MySQL database '{db_name}' on {host}:{port}...")
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset="utf8mb4",
                connect_timeout=5,
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.commit()
            conn.close()
            print(f"[OK] MySQL database '{db_name}' is ready.")
        except Exception as e:
            print(f"[ERROR] Could not connect to MySQL server to ensure database: {e}")
            print("Please verify your MySQL server is running and check credentials in .env file.")
            sys.exit(1)

    # Initialize SQLAlchemy tables
    try:
        init_db()
        print("[OK] All database tables successfully created/verified:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        print("\nDatabase initialization complete! You can now view these tables in MySQL Workbench.")
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_database()
