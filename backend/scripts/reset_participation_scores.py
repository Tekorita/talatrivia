"""Reset participation scores script."""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import app
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Imports must be after sys.path modification
from sqlalchemy import select, update  # noqa: E402

from app.infrastructure.db.models.participation import ParticipationModel  # noqa: E402
from app.infrastructure.db.session import AsyncSessionLocal  # noqa: E402


async def reset_participation_scores():
    """Reset all participation scores to 0."""
    async with AsyncSessionLocal() as session:
        # Get all participations
        result = await session.execute(select(ParticipationModel))
        participations = result.scalars().all()
        
        if not participations:
            print("No participations found.")
            return
        
        # Reset all scores to 0
        await session.execute(
            update(ParticipationModel)
            .values(score=0)
        )
        
        await session.commit()
        
        print(f"✓ Reset scores for {len(participations)} participation(s) to 0")
        print("\nUpdated participations:")
        for p in participations:
            print(f"  - Participation {p.id}: score reset to 0")


if __name__ == "__main__":
    asyncio.run(reset_participation_scores())
