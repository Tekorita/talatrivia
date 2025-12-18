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
  - `/admin/users` - Manage users (create players/admins)
  - `/admin/trivias` - Manage trivias (create and list trivias)
  - `/admin/trivias/:triviaId` - Trivia detail page with tabs:
    - Overview - View trivia metadata
    - Players - Assign players to trivia
    - Questions - Create and manage questions within trivia
    - Control - Start trivia, advance questions, view live ranking
  - `/admin/control` - Control gameplay (start trivia, advance questions, view live ranking) - Global control page
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

## Admin Dashboard

The Admin Dashboard provides a complete interface for managing the trivia game.

### Navigation

After logging in as ADMIN, you'll be redirected to `/admin/users`. The dashboard has a sidebar with three main sections:

1. **Users** - Create and manage players and admins
2. **Trivias** - Create and list trivia games
3. **Control (Live)** - Global control page for gameplay

### Trivia-Centric Flow

The admin workflow is now 100% trivia-centric:

1. **Create Trivia** (`/admin/trivias`)
   - Create a new trivia with title and description
   - Select players during creation
   - **Questions are NOT selected during creation** - they are added later from Trivia Detail
   - After successful creation, automatically navigates to the trivia detail page

2. **Open Trivia Detail** (`/admin/trivias/:triviaId`)
   - Click "Open" button on any trivia in the list
   - Navigate to the trivia detail page with tabs:
     - **Overview**: View trivia metadata (title, status, description, etc.)
     - **Players**: Assign players to this specific trivia
     - **Questions**: Create questions and associate them with this trivia (ONLY place to add questions)
     - **Control**: Start the trivia, advance questions, and view live ranking

3. **Manage Within Trivia**
   - All question creation happens ONLY within the trivia context (Trivia Detail → Questions tab)
   - Players are assigned to specific trivias
   - Control is per-trivia (though global control page still exists)

### Features

#### Users Page (`/admin/users`)

- View list of all users
- Create new users (players or admins) with:
  - Name
  - Email
  - Password
  - Role (PLAYER or ADMIN)

**Expected API endpoints:**
- `GET /users` - List all users
- `POST /users` - Create a new user

If endpoints are not available, the UI will show "Endpoint not available yet" without breaking.

#### Trivia Detail Page (`/admin/trivias/:triviaId`)

The trivia detail page provides a complete interface for managing a specific trivia with four tabs:

**Overview Tab:**
- Displays trivia metadata (title, description, status, current question index)
- Shows creation date and start time if available

**Players Tab:**
- View players assigned to this trivia
- Assign new players from available PLAYER users
- Two-column layout: Assigned Players | Available Players

**Expected API endpoints:**
- `GET /trivias/{id}/players` - List players assigned to trivia
- `POST /trivias/{id}/players` - Add player to trivia (body: `{ user_id }`)
- `GET /users` - List all users (to show available players)

**Questions Tab:**
- View questions associated with this trivia
- **This is the ONLY place to create and add questions to a trivia**
- Create new questions and automatically associate them with the trivia
- Form includes:
  - Question text
  - Difficulty (EASY, MEDIUM, HARD)
  - Minimum 4 options (can have more)
  - Exactly one correct option (enforced by UI)

**Expected API endpoints:**
- `GET /trivias/{id}/questions` - List questions associated with trivia
- `POST /questions` - Create a new question (body: `{ text, difficulty, options: [{ text, is_correct }] }`)
- `POST /trivias/{id}/questions` - Associate question with trivia (body: `{ question_id }`)

**Control Tab:**
- Start the trivia (calls `POST /trivias/{id}/start`)
- Advance to next question (calls `POST /trivias/{id}/next-question`)
- View live ranking (auto-refreshes every 3 seconds via `GET /trivias/{id}/ranking`)
- View current question details (via `GET /trivias/{id}/current-question`)

**Expected API endpoints:**
- `GET /trivias/{id}` - Get trivia by ID
- `POST /trivias/{id}/start` - Start trivia
- `POST /trivias/{id}/next-question` - Advance to next question
- `GET /trivias/{id}/ranking` - Get live ranking
- `GET /trivias/{id}/current-question` - Get current question

#### Trivias Page (`/admin/trivias`)

- View list of all trivias
- Create new trivias with:
  - Title
  - Description
  - Multiple player selection (from users with PLAYER role)
  - **Questions are NOT selected during creation** - they must be added from Trivia Detail → Questions tab
- After successful creation, automatically navigates to the trivia detail page
- Each trivia in the list has an "Open" button to navigate to the detail page

**Expected API endpoints:**
- `GET /trivias` - List all trivias
- `POST /trivias` - Create a new trivia (with title, description, user_ids; question_ids are optional)

**Note:** 
- Questions are managed ONLY from the Trivia Detail page (Questions tab)
- Players can also be managed from the Trivia Detail page after creation
- If the backend currently requires `question_ids`, a clear error message will be shown

#### Control Page (`/admin/control`) - Global Control

- Select active trivia from dropdown
- Start trivia (calls `POST /trivias/{id}/start`)
- Advance to next question (calls `POST /trivias/{id}/next-question`)
- View live ranking (auto-refreshes every 3 seconds via `GET /trivias/{id}/ranking`)
- View current question details (via `GET /trivias/{id}/current-question`)

**Features:**
- Live ranking updates automatically every 3 seconds
- Shows trivia status (LOBBY, IN_PROGRESS, FINISHED)
- Displays current question index
- Shows current question text and options (without correct answer)
- Time remaining display (if available)

**Active Trivia Selection:**
- The selected trivia is stored in the `ActiveTriviaContext`
- This allows the Control page to maintain state across navigation
- Select a trivia from the dropdown to start controlling it

### Endpoints Status

The dashboard gracefully handles missing endpoints:

- If a CRUD endpoint doesn't exist yet, the UI shows "Endpoint not available yet"
- The app continues to function normally
- No crashes or broken UI

### Workflow (100% Trivia-Centric)

1. **Create Users** (`/admin/users`)
   - Create player accounts that will participate in trivias

2. **Create Trivia** (`/admin/trivias`)
   - Create a new trivia with title and description
   - Select players during creation
   - **Do NOT select questions** - they will be added from Trivia Detail
   - After creation, automatically navigates to the trivia detail page

3. **Manage Trivia** (Trivia Detail - automatically opened after creation)
   - The trivia detail page opens automatically after creation
   - Or click "Open" on any trivia in the list to manage it

4. **Manage Players** (Trivia Detail → Players tab)
   - Assign players to the trivia from available PLAYER users
   - View currently assigned players

5. **Create Questions** (Trivia Detail → Questions tab)
   - **This is the ONLY place to add questions to a trivia**
   - Create questions within the trivia context
   - Questions are automatically associated with the trivia after creation
   - Each question requires:
     - Question text
     - Difficulty level (EASY, MEDIUM, HARD)
     - Minimum 4 options
     - Exactly one correct option (enforced by UI)

6. **Control Gameplay** (Trivia Detail → Control tab)
   - Start the trivia when ready
   - Advance through questions as players answer
   - Monitor live ranking to see scores in real-time (auto-updates every 3 seconds)
   - View current question details

**Alternative:** Use the global Control page (`/admin/control`) to manage any trivia from a central location.

