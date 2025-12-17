"""Seed script to create initial admin user."""
import asyncio
import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

# Add the parent directory to the Python path so we can import app
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Imports must be after sys.path modification
from app.core.password import hash_password  # noqa: E402
from app.infrastructure.db.models.user import UserModel, UserRole  # noqa: E402
from app.infrastructure.db.session import AsyncSessionLocal  # noqa: E402


async def seed_admin():
    """Create admin user if it doesn't exist."""
    # Get environment variables
    admin_email = os.getenv("ADMIN_EMAIL", "admin@test.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "Admin")
    
    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        result = await session.execute(
            select(UserModel).where(UserModel.email == admin_email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"Admin user with email {admin_email} already exists. Skipping seed.")
            return
        
        # Create admin user
        password_hash = hash_password(admin_password)
        admin_user = UserModel(
            id=uuid.uuid4(),
            name=admin_name,
            email=admin_email,
            password_hash=password_hash,
            role=UserRole.ADMIN,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print("Admin user created successfully:")
        print(f"  Email: {admin_email}")
        print(f"  Name: {admin_name}")
        print(f"  Role: {UserRole.ADMIN}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
