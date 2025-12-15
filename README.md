# Gemini Chat Application

A full-stack chat application built with FastAPI, Google ADK (Agent Development Kit), React, and DaisyUI.

## Features

- User authentication (JWT-based)
- Real-time streaming chat responses via SSE
- Conversation history with auto-generated titles
- Responsive UI with sidebar navigation
- **Supabase Integration** for persistent storage of users and chat sessions

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google ADK** - Agent Development Kit for managing AI agents
- **Supabase** - PostgreSQL database for users and sessions

### Frontend
- **React 18** - UI framework
- **React Router** - Client-side routing
- **DaisyUI 4** - Tailwind CSS component library
- **Vite** - Build tool

## Project Structure

```
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py            # Supabase client initialization
│   │   └── models.py        # User model class
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py        # Auth endpoints
│   │   ├── models.py        # Pydantic schemas
│   │   ├── utils.py         # Password hashing, JWT
│   │   └── dependencies.py  # Auth dependencies
│   ├── agent/
│   │   ├── __init__.py
│   │   └── agent.py         # Gemini agent configuration
│   └── chat/
│       ├── __init__.py
│       ├── routes.py        # Chat endpoints
│       ├── models.py        # Pydantic schemas
│       ├── service.py       # Chat service with ADK
│       └── supabase_session.py # ADK Session Service implementation
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── services/
│       │   └── api.js
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── hooks/
│       │   ├── useAuth.js
│       │   └── useChat.js
│       ├── components/
│       │   ├── Avatar.jsx
│       │   ├── Toast.jsx
│       │   ├── TypingIndicator.jsx
│       │   ├── ChatMessage.jsx
│       │   ├── ChatInput.jsx
│       │   ├── ChatArea.jsx
│       │   ├── Sidebar.jsx
│       │   ├── Navbar.jsx
│       │   └── Layout.jsx
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Register.jsx
│       │   └── Chat.jsx
│       └── assets/
│           ├── user-avatar.svg
│           └── agent-avatar.svg
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Cloud API Key with Gemini API access
- Supabase Account and Project

### Supabase Setup

Create the following tables in your Supabase project:

1. **users**
   - `id` (uuid, primary key)
   - `username` (text, unique)
   - `hashed_password` (text)
   - `created_at` (timestamptz)

2. **sessions**
   - `id` (text, primary key)
   - `app_name` (text)
   - `user_id` (text)
   - `state` (jsonb)
   - `last_update_time` (timestamptz)

3. **events**
   - `id` (int8/uuid, primary key, auto-generated)
   - `session_id` (text, foreign key to sessions.id)
   - `event_data` (jsonb)
   - `created_at` (timestamptz)

### Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:
- `GOOGLE_API_KEY` - Your Google API key for Gemini
- `SECRET_KEY` - Secret key for JWT tokens (generate a random string)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase `anon` public key

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173` and will proxy API requests to the backend at `http://localhost:8000`.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Sessions
- `GET /api/sessions` - List user's chat sessions
- `GET /api/sessions/{id}` - Get session with messages

### Chat
- `POST /api/chat` - Send message and receive streaming response (SSE)

## SSE Events

The chat endpoint streams responses using Server-Sent Events:

- `session` - `{session_id, is_new}` - Session info
- `delta` - `{content}` - Streamed text chunk
- `title` - `{title}` - Auto-generated title (for new sessions)
- `done` - `{}` - Stream complete
- `error` - `{message}` - Error occurred

## Development

### Running Both Servers

In one terminal:
```bash
uvicorn backend.main:app --reload --port 8000
```

In another terminal:
```bash
cd frontend && npm run dev
```

### Building for Production

```bash
# Build frontend
cd frontend && npm run build

# The built files will be in frontend/dist
# The FastAPI app can serve these static files
```

## License

MIT
