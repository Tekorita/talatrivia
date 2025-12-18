"""Update player passwords with proper bcrypt hashes."""
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


async def update_player_passwords():
    """Update passwords for players with incorrect hash."""
    # Get environment variable or use default
    player_password = os.getenv("PLAYER_PASSWORD", "player123")
    
    async with AsyncSessionLocal() as session:
        # Get all players with incorrect password hash
        result = await session.execute(
            select(UserModel).where(
                UserModel.role == "PLAYER",
                UserModel.password_hash == "hash"
            )
        )
        players = result.scalars().all()
        
        if not players:
            print("No players found with incorrect password hash.")
            return
        
        # Generate new hash
        new_hash = hash_password(player_password)
        
        print(f"Found {len(players)} player(s) with incorrect password hash.")
        print(f"Setting password to: {player_password}")
        print()
        
        for player in players:
            old_hash = player.password_hash
            player.password_hash = new_hash
            print(f"Updated password for: {player.name} ({player.email})")
            print(f"  Old hash: {old_hash}")
            print(f"  New hash: {new_hash[:30]}...")
        
        await session.commit()
        print()
        print("✓ Passwords updated successfully!")
        print(f"All players can now login with password: {player_password}")


if __name__ == "__main__":
    asyncio.run(update_player_passwords())
