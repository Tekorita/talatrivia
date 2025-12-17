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

## Routes

### Public Routes
- `/login` - Login page (MVP)

### Protected Routes
- `/admin` - Admin dashboard (requires ADMIN role)
- `/player/lobby` - Player lobby (requires PLAYER role)

### Smart Redirect
- `/` - Automatically redirects based on session:
  - If logged in as ADMIN → `/admin`
  - If logged in as PLAYER → `/player/lobby`
  - If not logged in → `/login`

## Testing Login

The login now uses email and password authentication against the backend API.

### Prerequisites

1. Make sure the backend is running and the database is set up
2. Seed the admin user (see backend README for details):
```bash
docker compose -f docker-compose-local.yml exec backend python scripts/seed_admin.py
```

### Default Admin Credentials

- **Email:** `admin@test.com`
- **Password:** `admin123`

(These can be customized via environment variables in `docker-compose-local.yml`)

### Testing Steps

1. Start the application:
```bash
docker compose -f docker-compose-local.yml up --build
```

2. Navigate to `http://localhost:5173/login`

3. Test as ADMIN:
   - Enter email: `admin@test.com`
   - Enter password: `admin123`
   - Click "Login"
   - Should redirect to `/admin`

4. Test session persistence:
   - After logging in, refresh the browser
   - Session should persist and you should remain on the same page

5. Test logout:
   - Click "Logout" button on any dashboard
   - Should redirect to `/login`
   - Session should be cleared

6. Test error handling:
   - Try logging in with invalid credentials
   - Should show "Invalid email or password" error message

