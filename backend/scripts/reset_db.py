"""Reset database - truncate all tables."""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

# Add the parent directory to the Python path so we can import app
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Imports must be after sys.path modification
from app.infrastructure.db.session import AsyncSessionLocal  # noqa: E402


async def reset_db():
    """Reset database by truncating all tables."""
    async with AsyncSessionLocal() as session:
        try:
            # Get all table names from the public schema
            result = await session.execute(
                text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("No tables found in database.")
                return
            
            # Build TRUNCATE statement with CASCADE to handle foreign keys
            table_list = ", ".join(f'"{table}"' for table in tables)
            truncate_sql = f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;"
            
            await session.execute(text(truncate_sql))
            await session.commit()
            
            print(f"Truncated {len(tables)} tables: {', '.join(tables)}")
            print("DB reset OK")
            
        except Exception as e:
            await session.rollback()
            print(f"Error resetting database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(reset_db())
