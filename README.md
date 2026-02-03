# Dynamic Memory System

A full-stack chat application built with FastAPI, Google ADK (Agent Development Kit), React, and DaisyUI.

Remembers User persona across various conversations and builds a timeline of user activities. 
This is achieved using context engineering techniques like entity extraction, llm as orchestrator & state resolver, tool calling

## Features

- A ChatGPT style chat UI that has Real-time streaming chat responses via SSE
- Conversation history with auto-generated titles
- Responsive UI with sidebar navigation
- **Supabase Integration** for persistent storage of users and chat sessions
- **Mongodb Integration** for storing user's persona and activity timeline
- JWT-based User authentication

The moat of this project can be found at `https://github.com/AdityaSanthosh/UserMemory-Chat/blob/main/backend/agent/agent.py`

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
