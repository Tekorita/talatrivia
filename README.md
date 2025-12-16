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

- `GET /health` - Health check endpoint

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

## Tareas de VSCode/Cursor

Desde el directorio `backend/`, puedes usar las tareas configuradas en `.vscode/tasks.json`:

- **Docker Compose: Up** - Levanta los servicios
- **Docker Compose: Down** - Detiene los servicios
- **Alembic: Upgrade Head** - Aplica migraciones
- **Alembic: Create Migration** - Crea una nueva migración

