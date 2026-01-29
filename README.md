# CherriesService

Backend API service for the Cherries mobile app - helping users conquer their quests through daily check-ins.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Supabase Auth
- **Deployment**: Railway

## Project Structure

```
CherriesService/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   │       ├── auth.py      # Authentication routes
│   │       ├── quests.py    # Quest management routes
│   │       └── checkins.py  # Check-in routes
│   ├── core/
│   │   ├── config.py        # Application configuration
│   │   ├── supabase.py      # Supabase client setup
│   │   └── utils.py         # Utility functions
│   ├── models/              # Database models (if using ORM)
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── quest.py
│   │   └── checkin.py
│   ├── services/            # Business logic
│   └── main.py              # FastAPI app entry point
├── tests/                   # Test files
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment variables
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## Setup

### 1. Clone the repository

```bash
cd ~/Projects/CherriesService
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

Update the following variables in `.env`:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `SECRET_KEY`: Generate a secure random string

### 5. Set up Supabase database

Run the SQL migrations in your Supabase SQL editor (see Database Schema section below).

### 6. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Database Schema

You'll need to create the following tables in your Supabase database:

### Tables

**quests**
- id (uuid, primary key)
- name (text)
- description (text, nullable)
- start_date (date)
- end_date (date)
- creator_id (uuid, references auth.users)
- share_code (text, unique)
- share_code_expires_at (timestamp)
- created_at (timestamp)
- updated_at (timestamp)

**daily_tasks**
- id (uuid, primary key)
- quest_id (uuid, references quests)
- title (text)
- description (text, nullable)
- points (integer, default 10)
- created_at (timestamp)

**quest_participants**
- quest_id (uuid, references quests)
- user_id (uuid, references auth.users)
- joined_at (timestamp)
- total_points (integer, default 0)
- primary key (quest_id, user_id)

**check_ins**
- id (uuid, primary key)
- user_id (uuid, references auth.users)
- quest_id (uuid, references quests)
- daily_task_id (uuid, references daily_tasks)
- check_in_date (date)
- points_earned (integer)
- notes (text, nullable)
- created_at (timestamp)

See `database/schema.sql` for the complete SQL schema.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user

### Quests
- `POST /api/v1/quests` - Create a new quest
- `GET /api/v1/quests` - Get all user's quests
- `GET /api/v1/quests/{quest_id}` - Get specific quest
- `POST /api/v1/quests/join` - Join quest via share code

### Check-ins
- `POST /api/v1/checkins` - Create a check-in
- `GET /api/v1/checkins/quest/{quest_id}` - Get quest check-ins
- `GET /api/v1/checkins/stats/{quest_id}` - Get check-in statistics

## Deployment

### Railway Deployment

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy

Railway will automatically detect the Python project and deploy it.

## Development

### Running tests

```bash
pytest
```

### Code formatting

```bash
black app/
```

### Type checking

```bash
mypy app/
```

## License

Proprietary - Cherries App
