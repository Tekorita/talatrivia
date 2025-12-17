# TalaTrivia Frontend

Frontend application for TalaTrivia built with React + TypeScript + Vite.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Update `VITE_API_URL` in `.env` if needed (default: `http://localhost:8000`)

## Development

Run the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Docker

Build and run with Docker Compose (from project root):
```bash
docker compose -f docker-compose-local.yml up --build frontend
```

The frontend will be available at `http://localhost:5173`

