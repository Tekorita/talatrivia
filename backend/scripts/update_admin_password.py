"""Update admin user password hash."""
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select

# Add the parent directory to the Python path so we can import app
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Imports must be after sys.path modification
from app.core.password import hash_password  # noqa: E402
from app.infrastructure.db.models.user import UserModel  # noqa: E402
from app.infrastructure.db.session import AsyncSessionLocal  # noqa: E402


async def update_admin_password():
    """Update admin user password hash."""
    # Get environment variables
    admin_email = os.getenv("ADMIN_EMAIL", "admin@test.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    async with AsyncSessionLocal() as session:
        # Find admin user
        result = await session.execute(
            select(UserModel).where(UserModel.email == admin_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User with email {admin_email} not found.")
            return
        
        # Update password hash
        password_hash = hash_password(admin_password)
        user.password_hash = password_hash
        
        await session.commit()
        
        print("Password updated successfully for user:")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.name}")
        print(f"  Role: {user.role}")


if __name__ == "__main__":
    asyncio.run(update_admin_password())
