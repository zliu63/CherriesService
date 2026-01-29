# CherriesService Quick Start Guide

## Prerequisites

- Python 3.9 or higher
- Supabase account (free tier is fine)
- Git

## Step 1: Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the database to be ready
3. Go to Project Settings > API
4. Copy these values:
   - Project URL
   - anon/public key
   - service_role key (keep this secret!)

## Step 2: Create Database Tables

1. In your Supabase dashboard, go to SQL Editor
2. Copy the entire contents of `database/schema.sql`
3. Paste and run it in the SQL Editor
4. Verify tables are created in the Table Editor

## Step 3: Local Setup

```bash
# Navigate to project directory
cd ~/Projects/CherriesService

# Create virtual environment
pyenv virtualenv 3.12.10 cherries-service
pyenv activate cherries-service

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

## Step 4: Configure Environment

Edit `.env` and add your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
SECRET_KEY=generate_a_random_secret_here
```

To generate a secure SECRET_KEY, run:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 5: Run the Server

```bash
# Using the run script
./run.sh

# Or manually
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/v1/docs
- Health: http://localhost:8000/health

## Step 6: Test the API

### Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!",
    "username": "testuser"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!"
  }'
```

Save the `access_token` from the response!

### Create a Quest

```bash
curl -X POST http://localhost:8000/api/v1/quests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "30 Day Fitness Challenge",
    "description": "Get fit in 30 days",
    "start_date": "2026-02-01",
    "end_date": "2026-03-02",
    "daily_tasks": [
      {
        "title": "Morning Run",
        "description": "Run for 30 minutes",
        "points": 20
      },
      {
        "title": "Drink Water",
        "description": "Drink 8 glasses of water",
        "points": 10
      }
    ]
  }'
```

## Step 7: Deploy to Railway (Optional)

1. Create account on [railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Add environment variables in Railway dashboard
4. Deploy!

## Troubleshooting

### "Module not found" error
Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### "Connection refused" to Supabase
Check your SUPABASE_URL and keys in `.env`

### "Unauthorized" errors
Make sure you're including the Bearer token in Authorization header

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API docs at http://localhost:8000/api/v1/docs
- Start building the iOS app!

## Support

For issues or questions, check:
- Supabase docs: https://supabase.com/docs
- FastAPI docs: https://fastapi.tiangolo.com
- Railway docs: https://docs.railway.app
