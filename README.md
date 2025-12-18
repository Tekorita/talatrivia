# TalaTrivia

Monorepo for the TalaTrivia trivia game, built with FastAPI (backend) and Hexagonal Architecture.

## Project Structure

```
talatrivia/
├── backend/              # Backend API (FastAPI + PostgreSQL)
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── core/                   # Core configuration and utilities
│   │   ├── domain/                 # Domain layer (entities, ports)
│   │   ├── application/            # Use cases
│   │   └── infrastructure/         # Adapters (DB, API)
│   ├── alembic/                    # Database migrations
│   ├── tests/                      # Tests (pytest ready)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Frontend (React + TypeScript)
├── docker-compose-local.yml  # Service orchestration
└── CHANGELOG.md
```

## Requirements

- Python 3.12
- Docker and Docker Compose
- PostgreSQL 15 or 16

## Initial Setup

### Steps to Start the Project

**1. Start the project with Docker Compose (from the project root):**

```bash
docker compose -f docker-compose-local.yml up --build
```

This command builds and starts all services (PostgreSQL, Backend, Frontend).

**2. Run migrations and create tables:**

```bash
docker compose -f docker-compose-local.yml exec backend alembic upgrade head
```

This command applies all Alembic migrations and creates the database tables.

**3. Load initial data (users, trivias, questions):**

```bash
docker compose -f docker-compose-local.yml exec backend python scripts/seed_db.py
```

This command loads all initial data from `backend/seed/seed_data.json`.

### User Credentials

Once you've completed the steps above, you can log in with any of these users:

**Administrator:**
- Email: `admin@test.com`
- Password: `123`

**Player 1:**
- Email: `player1@test.com`
- Password: `123`

**Player 2:**
- Email: `player2@test.com`
- Password: `123`

### Ready to Use!

**With these 3 steps, the project is completely configured and ready to use.** 

- Frontend available at: `http://localhost:3000`
- Backend API available at: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

## Local Development (without Docker)

For local backend development with debug in VSCode/Cursor:

1. Make sure PostgreSQL is running locally
2. Adjust `DATABASE_URL` in `backend/.env` to point to `localhost:5432`
3. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

4. Run migrations:

```bash
cd backend
alembic upgrade head
```

5. Use the debug configuration in `backend/.vscode/launch.json` to run the application

## Backend

### Endpoints

#### Health
- `GET /health` - Health check endpoint

#### Auth
- `POST /auth/login` - Authenticate user with email and password
  - Body: `{ "email": "user@example.com", "password": "password" }`
  - Returns: `{ "id": "uuid", "name": "User Name", "email": "user@example.com", "role": "ADMIN" | "PLAYER" }`
  - Errors:
    - `401` - Invalid email or password
    - `404` - User not found

#### Lobby
- `POST /trivias/{trivia_id}/join` - Join a trivia
  - Body: `{ "user_id": "uuid" }`
- `POST /trivias/{trivia_id}/ready` - Set participant as ready
  - Body: `{ "user_id": "uuid" }`
- `POST /trivias/{trivia_id}/start` - Start a trivia (admin only)
  - Body: `{ "admin_user_id": "uuid" }`

#### Gameplay
- `GET /trivias/{trivia_id}/current-question?user_id={uuid}` - Get current question
  - Returns: Question with options (without correct answer) and time remaining
- `POST /trivias/{trivia_id}/answer` - Submit an answer
  - Body: `{ "user_id": "uuid", "selected_option_id": "uuid" }`
  - Returns: Answer result with correctness, earned points, and total score

### Architecture

The backend follows Hexagonal Architecture (Ports & Adapters) and SOLID principles:

- **Domain**: Pure domain entities (no infrastructure dependencies)
- **Application**: Use cases that orchestrate business logic
- **Infrastructure**: Adapters for database and API

### Migrations

To create a new migration:

```bash
docker compose -f docker-compose-local.yml exec backend alembic revision --autogenerate -m "description"
```

To apply migrations:

```bash
docker compose -f docker-compose-local.yml exec backend alembic upgrade head
```

## Authentication

The system uses simple email and password authentication. Users are created automatically when running the seed script (`scripts/seed_db.py`).

### Test Login (API)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "123"}'
```

## Testing Lobby Endpoints

Test data (users and trivias) is created automatically when running `scripts/seed_db.py` (see Initial Setup section).

If you need to create additional data manually, you can use DBeaver or psql:

2. **Test endpoints** (using curl or Postman):
   ```bash
   # Join trivia
   curl -X POST http://localhost:8000/trivias/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/join \
     -H "Content-Type: application/json" \
     -d '{"user_id": "22222222-2222-2222-2222-222222222222"}'
   
   # Set ready
   curl -X POST http://localhost:8000/trivias/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/ready \
     -H "Content-Type: application/json" \
     -d '{"user_id": "22222222-2222-2222-2222-222222222222"}'
   
   # Start trivia (admin)
   curl -X POST http://localhost:8000/trivias/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/start \
     -H "Content-Type: application/json" \
     -d '{"admin_user_id": "11111111-1111-1111-1111-111111111111"}'
   
   # Get current question
   curl -X GET "http://localhost:8000/trivias/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/current-question?user_id=22222222-2222-2222-2222-222222222222"
   
   # Submit answer
   curl -X POST http://localhost:8000/trivias/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/answer \
     -H "Content-Type: application/json" \
     -d '{"user_id": "22222222-2222-2222-2222-222222222222", "selected_option_id": "option-uuid-here"}'
   ```

## VSCode/Cursor Tasks

From the `backend/` directory, you can use the tasks configured in `.vscode/tasks.json`:

- **Docker Compose: Up** - Start services
- **Docker Compose: Down** - Stop services
- **Alembic: Upgrade Head** - Apply migrations
- **Alembic: Create Migration** - Create a new migration

