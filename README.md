# TalaTrivia

Monorepo para el juego de trivia TalaTrivia, construido con FastAPI (backend) y Arquitectura Hexagonal.

## Estructura del Proyecto

```
talatrivia/
├── backend/              # Backend API (FastAPI + PostgreSQL)
│   ├── app/
│   │   ├── main.py                 # Punto de entrada FastAPI
│   │   ├── core/                   # Configuración y utilidades core
│   │   ├── domain/                 # Capa de dominio (entidades, puertos)
│   │   ├── application/            # Casos de uso
│   │   └── infrastructure/         # Adaptadores (DB, API)
│   ├── alembic/                    # Migraciones de base de datos
│   ├── tests/                      # Tests (preparado para pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Frontend (a implementar)
├── docker-compose-local.yml  # Orquestación de servicios
└── CHANGELOG.md
```

## Requisitos

- Python 3.12
- Docker y Docker Compose
- PostgreSQL 15 o 16

## Configuración Inicial

1. Configura las variables de entorno del backend:

```bash
cd backend
cp .env.example .env
# Ajusta las variables según tu entorno
```

2. Construye y levanta los servicios con Docker Compose (desde la raíz):

```bash
docker compose -f docker-compose-local.yml up --build
```

3. Ejecuta las migraciones de Alembic:

```bash
docker compose -f docker-compose-local.yml exec backend alembic upgrade head
```

4. Crea el usuario admin inicial:

```bash
docker compose -f docker-compose-local.yml exec backend python scripts/seed_admin.py
```

O alternativamente, usando PYTHONPATH:

```bash
docker compose -f docker-compose-local.yml exec backend sh -c "PYTHONPATH=/app python scripts/seed_admin.py"
```

El script usa las siguientes variables de entorno (configuradas en `docker-compose-local.yml`):
- `ADMIN_EMAIL` (default: `admin@test.com`)
- `ADMIN_PASSWORD` (default: `admin123`)
- `ADMIN_NAME` (default: `Admin`)

Si el usuario admin ya existe, el script no hará nada.

## Desarrollo Local (sin Docker)

Para desarrollo local del backend con debug en VSCode/Cursor:

1. Asegúrate de tener PostgreSQL corriendo localmente
2. Ajusta `DATABASE_URL` en `backend/.env` para apuntar a `localhost:5432`
3. Instala las dependencias:

```bash
cd backend
pip install -r requirements.txt
```

4. Ejecuta las migraciones:

```bash
cd backend
alembic upgrade head
```

5. Usa la configuración de debug en `backend/.vscode/launch.json` para correr la aplicación

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

### Arquitectura

El backend sigue Arquitectura Hexagonal (Ports & Adapters) y principios SOLID:

- **Domain**: Entidades de dominio puras (sin dependencias de infraestructura)
- **Application**: Casos de uso que orquestan la lógica de negocio
- **Infrastructure**: Adaptadores para base de datos y API

### Migraciones

Para crear una nueva migración:

```bash
docker compose -f docker-compose-local.yml exec backend alembic revision --autogenerate -m "descripción"
```

Para aplicar migraciones:

```bash
docker compose -f docker-compose-local.yml exec backend alembic upgrade head
```

## Autenticación

El sistema usa autenticación simple con email y password (sin JWT por ahora, pero preparado para agregarlo después).

### Crear Usuario Admin

Para crear el usuario admin inicial, ejecuta:

```bash
docker compose -f docker-compose-local.yml exec backend python scripts/seed_admin.py
```

Esto creará un usuario admin con las credenciales configuradas en `docker-compose-local.yml`:
- Email: `admin@test.com` (configurable via `ADMIN_EMAIL`)
- Password: `admin123` (configurable via `ADMIN_PASSWORD`)
- Name: `Admin` (configurable via `ADMIN_NAME`)

El script es idempotente: si el usuario ya existe, no hará nada.

### Probar Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'
```

## Pruebas de Endpoints de Lobby

Para probar los endpoints de lobby, primero necesitas crear datos de prueba en la base de datos:

1. **Crear usuarios y trivia en la base de datos** (puedes usar DBeaver o psql):
   ```sql
   -- Nota: Los usuarios ahora deben tener password_hash válido (usar el script seed_admin.py o generar hash con bcrypt)
   -- Crear trivia (asumiendo que ya tienes un admin creado con el script seed_admin.py)
   INSERT INTO trivias (id, title, description, created_by_user_id, status, current_question_index, created_at)
   VALUES 
     ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Test Trivia', 'Test Description', 
      '<admin-user-id-from-seed>', 'LOBBY', 0, NOW());
   ```

2. **Probar endpoints** (usando curl o Postman):
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

## Tareas de VSCode/Cursor

Desde el directorio `backend/`, puedes usar las tareas configuradas en `.vscode/tasks.json`:

- **Docker Compose: Up** - Levanta los servicios
- **Docker Compose: Down** - Detiene los servicios
- **Alembic: Upgrade Head** - Aplica migraciones
- **Alembic: Create Migration** - Crea una nueva migración

