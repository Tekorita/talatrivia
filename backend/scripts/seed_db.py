"""Seed database with data from seed_data.json."""
import asyncio
import json
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
from app.infrastructure.db.models.option import OptionModel  # noqa: E402
from app.infrastructure.db.models.participation import ParticipationModel  # noqa: E402
from app.infrastructure.db.models.question import QuestionModel  # noqa: E402
from app.infrastructure.db.models.trivia import TriviaModel  # noqa: E402
from app.infrastructure.db.models.trivia_question import TriviaQuestionModel  # noqa: E402
from app.infrastructure.db.models.user import UserModel  # noqa: E402
from app.infrastructure.db.session import AsyncSessionLocal  # noqa: E402


def validate_question(question_data: dict) -> None:
    """Validate question structure."""
    if len(question_data["options"]) != 4:
        raise ValueError(f"Question '{question_data['text']}' must have exactly 4 options, got {len(question_data['options'])}")
    
    correct_count = sum(1 for opt in question_data["options"] if opt["is_correct"])
    if correct_count != 1:
        raise ValueError(f"Question '{question_data['text']}' must have exactly 1 correct option, got {correct_count}")
    
    if question_data["difficulty"] not in ["EASY", "MEDIUM", "HARD"]:
        raise ValueError(f"Question '{question_data['text']}' has invalid difficulty: {question_data['difficulty']}")


async def seed_db():
    """Seed database with data from seed_data.json."""
    # Load seed data
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    seed_file = backend_dir / "seed" / "seed_data.json"
    if not seed_file.exists():
        print(f"Error: Seed file not found at {seed_file}")
        return
    
    with open(seed_file, encoding="utf-8") as f:
        seed_data = json.load(f)
    
    # Validate all questions first
    for question_data in seed_data["questions"]:
        validate_question(question_data)
    
    async with AsyncSessionLocal() as session:
        try:
            # Counters
            users_created = 0
            trivias_created = 0
            participations_created = 0
            questions_created = 0
            options_created = 0
            
            # Maps for lookups
            email_to_user_id = {}
            trivia_title_to_id = {}
            question_text_to_id = {}
            
            # 1. Create users
            print("Creating users...")
            admin_user_id = None
            for user_data in seed_data["users"]:
                # Check if user already exists
                result = await session.execute(
                    select(UserModel).where(UserModel.email == user_data["email"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    user_id = existing_user.id
                    print(f"  User {user_data['email']} already exists, skipping")
                else:
                    user = UserModel(
                        id=uuid.uuid4(),
                        name=user_data["name"],
                        email=user_data["email"],
                        password_hash=hash_password(user_data["password_plain"]),
                        role=user_data["role"],
                    )
                    session.add(user)
                    user_id = user.id
                    users_created += 1
                
                email_to_user_id[user_data["email"]] = user_id
                if user_data["role"] == "ADMIN":
                    admin_user_id = user_id
            
            if not admin_user_id:
                raise ValueError("No ADMIN user found in seed data. At least one ADMIN user is required.")
            
            await session.flush()
            
            # 2. Create trivias
            print("Creating trivias...")
            for trivia_data in seed_data["trivias"]:
                trivia = TriviaModel(
                    id=uuid.uuid4(),
                    title=trivia_data["title"],
                    description=trivia_data["description"],
                    created_by_user_id=admin_user_id,
                    status=trivia_data.get("status", "DRAFT"),
                    current_question_index=0,
                )
                session.add(trivia)
                await session.flush()
                trivia_title_to_id[trivia_data["title"]] = trivia.id
                trivias_created += 1
            
            await session.flush()
            
            # 3. Create participations (assign players to trivias)
            print("Creating participations...")
            for trivia_data in seed_data["trivias"]:
                trivia_id = trivia_title_to_id[trivia_data["title"]]
                for player_email in trivia_data["players_emails"]:
                    if player_email not in email_to_user_id:
                        print(f"  Warning: Player {player_email} not found in users, skipping participation")
                        continue
                    
                    user_id = email_to_user_id[player_email]
                    
                    # Check if participation already exists
                    result = await session.execute(
                        select(ParticipationModel).where(
                            ParticipationModel.trivia_id == trivia_id,
                            ParticipationModel.user_id == user_id,
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        participation = ParticipationModel(
                            id=uuid.uuid4(),
                            trivia_id=trivia_id,
                            user_id=user_id,
                            status="INVITED",
                            score=0,
                        )
                        session.add(participation)
                        participations_created += 1
            
            await session.flush()
            
            # 4. Create questions and options
            print("Creating questions and options...")
            for question_data in seed_data["questions"]:
                # Create question
                question = QuestionModel(
                    id=uuid.uuid4(),
                    text=question_data["text"],
                    difficulty=question_data["difficulty"],
                    created_by_user_id=admin_user_id,
                )
                session.add(question)
                await session.flush()
                question_id = question.id
                question_text_to_id[question_data["text"]] = question_id
                questions_created += 1
                
                # Create options for this question
                for option_data in question_data["options"]:
                    option = OptionModel(
                        id=uuid.uuid4(),
                        question_id=question_id,
                        text=option_data["text"],
                        is_correct=option_data["is_correct"],
                    )
                    session.add(option)
                    options_created += 1
            
            await session.flush()
            
            # 5. Associate questions to trivias (create TriviaQuestion)
            print("Associating questions to trivias...")
            trivia_question_positions = {}  # Track position per trivia
            
            for question_data in seed_data["questions"]:
                trivia_title = question_data["trivia_title"]
                if trivia_title not in trivia_title_to_id:
                    print(f"  Warning: Trivia '{trivia_title}' not found, skipping question association")
                    continue
                
                trivia_id = trivia_title_to_id[trivia_title]
                question_id = question_text_to_id[question_data["text"]]
                
                # Get current position for this trivia
                if trivia_id not in trivia_question_positions:
                    trivia_question_positions[trivia_id] = 0
                
                position = trivia_question_positions[trivia_id]
                
                # Check if association already exists
                result = await session.execute(
                    select(TriviaQuestionModel).where(
                        TriviaQuestionModel.trivia_id == trivia_id,
                        TriviaQuestionModel.question_id == question_id,
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    trivia_question = TriviaQuestionModel(
                        id=uuid.uuid4(),
                        trivia_id=trivia_id,
                        question_id=question_id,
                        position=position,
                        time_limit_seconds=30,  # Default time limit
                    )
                    session.add(trivia_question)
                
                trivia_question_positions[trivia_id] += 1
            
            # Commit all changes
            await session.commit()
            
            # Print summary
            print("\n" + "=" * 50)
            print("Seed completed successfully!")
            print("=" * 50)
            print(f"Usuarios creados: {users_created}")
            print(f"Trivias creadas: {trivias_created}")
            print(f"Participations creadas: {participations_created}")
            print(f"Preguntas creadas: {questions_created}")
            print(f"Opciones creadas: {options_created}")
            print("=" * 50)
            
        except Exception as e:
            await session.rollback()
            print(f"\nError seeding database: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(seed_db())
