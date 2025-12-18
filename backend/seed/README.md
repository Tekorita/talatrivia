# Seed Data

Este directorio contiene los datos de inicialización (seed) para la base de datos.

## Archivos

- `seed_data.json`: Archivo JSON con usuarios, trivias y preguntas para poblar la base de datos.

## Scripts

### Reset Database

Vacía todas las tablas de la base de datos:

```bash
docker compose -f docker-compose-local.yml exec backend python scripts/reset_db.py
```

O desde el host (si tienes acceso directo):

```bash
cd backend
python scripts/reset_db.py
```

### Seed Database

Pobla la base de datos con los datos del archivo `seed_data.json`:

```bash
docker compose -f docker-compose-local.yml exec backend python scripts/seed_db.py
```

O desde el host:

```bash
cd backend
python scripts/seed_db.py
```

## Flujo recomendado

Para resetear y poblar la base de datos desde cero:

```bash
# 1. Resetear la base de datos (vacía todas las tablas)
docker compose -f docker-compose-local.yml exec backend python scripts/reset_db.py

# 2. Poblar con datos de seed
docker compose -f docker-compose-local.yml exec backend python scripts/seed_db.py
```

## Estructura del seed_data.json

```json
{
  "users": [
    {
      "name": "Nombre",
      "email": "email@test.com",
      "role": "ADMIN|PLAYER",
      "password_plain": "contraseña en texto plano"
    }
  ],
  "trivias": [
    {
      "title": "Título de la trivia",
      "description": "Descripción",
      "players_emails": ["player1@test.com", "player2@test.com"]
    }
  ],
  "questions": [
    {
      "trivia_title": "Título de la trivia (debe coincidir con una trivia)",
      "text": "Texto de la pregunta",
      "difficulty": "EASY|MEDIUM|HARD",
      "options": [
        {
          "text": "Opción 1",
          "is_correct": true
        },
        {
          "text": "Opción 2",
          "is_correct": false
        },
        {
          "text": "Opción 3",
          "is_correct": false
        },
        {
          "text": "Opción 4",
          "is_correct": false
        }
      ]
    }
  ]
}
```

## Validaciones

Los scripts validan automáticamente:

- Cada pregunta debe tener exactamente 4 opciones
- Cada pregunta debe tener exactamente 1 opción correcta
- La dificultad debe ser EASY, MEDIUM o HARD
- Los emails de players en trivias deben existir en la lista de users
