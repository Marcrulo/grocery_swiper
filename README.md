# Grocery Swiper

Flask app that serves swipeable grocery products and exposes a read-only SQLite database API on the same server/port.

## Run the app

1. Create/activate the project virtualenv and install deps.
2. Initialize the SQLite DB.
3. Start the Flask server.

### Quick start

```bash
# 1) Activate project venv (adjust if already active)
source .venv/bin/activate

# 2) Initialize database (creates data/sql/swipes.db)
python data/sql/init_db.py

# 3) Run the server (port 8000)
python app/app.py
```

Then open http://localhost:8000 to use the app.

## Database API (read-only)

- `/api/db`: Basic DB info and table list.
- `/api/db/tables`: List non-internal tables.
- `/api/db/download`: Download the raw SQLite file.
	- Tip: `curl -OJ http://localhost:8000/api/db/download` uses server-provided filename.
	- Or `curl -O http://localhost:8000/api/db/swipes.db` (filename embedded in URL).
- `/api/db/select` (POST JSON): Execute SELECT-only queries.

Examples:

```bash
# DB info
curl http://localhost:8000/api/db

# Tables
curl http://localhost:8000/api/db/tables

# Read-only query (limit enforced)
curl -X POST http://localhost:8000/api/db/select \
	-H 'Content-Type: application/json' \
	-d '{"sql": "SELECT * FROM swipes ORDER BY created_at DESC", "limit": 50}'
```

Notes:
- Only single `SELECT` statements are allowed; no writes.
- The DB file path is at `data/sql/swipes.db`.