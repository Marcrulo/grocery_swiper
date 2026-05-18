# Grocery Swiper 🛒

Grocery Swiper is a three-step pipeline that turns weekly grocery flyers into a swipe-based preference dataset and a personalized recommendation email.
The project is split into:

1) data collection + processing
2) a Tinder-like swipe app for labeling
3) a recommender + email notification system

Blog context (Part 1-3):
- https://marcrulo.github.io/MonthlyProjects/grocery-swiper-part1
- https://marcrulo.github.io/MonthlyProjects/grocery-swiper-part2
- https://marcrulo.github.io/MonthlyProjects/grocery-swiper-part3

## Step 1: Scrape weekly offers and process data 🧹

Goal: build a growing dataset of grocery items from weekly flyers.

What happens:
- Scrape flyer items from tilbudsugen.dk, including hidden metadata exposed in JSON payloads.
- Save raw data as CSV, download images, and create enriched item features.
- Processed outputs are stored alongside raw snapshots for historical tracking.
- A GitHub Actions workflow runs the scrape + processing on a weekly schedule to keep the dataset fresh.

Where in code:
- [scripts/scrape.py](scripts/scrape.py): scraping logic for weekly offers.
- [scripts/processing.py](scripts/processing.py): feature processing and image handling.
- [data/csv/raw](data/csv/raw) and [data/csv/processed](data/csv/processed): saved weekly snapshots.

## Step 2: Swipe app to gather preferences 📱

Goal: collect like/pass/super-like labels from real users.

What happens:
- A lightweight web app mimics a mobile swipe experience.
- Users swipe on items to generate preference labels that are stored in a local database.
- The UI keeps history for revisions and includes a full-screen mode to feel more app-like.

Where in code:
- [app/app.py](app/app.py): Flask app and API endpoints.
- [templates/index.html](templates/index.html): app layout.
- [app/static/script.js](app/static/script.js): swipe logic + client-side behavior.
- [app/static/style.css](app/static/style.css): UI styling.
- [sql/init_db.py](sql/init_db.py): database initialization.

## Step 3: Recommender + email notifications 🤖

Goal: learn preferences from the swipe data, rank new items, and send weekly recommendations.

What happens:
- Train a preference model on engineered features (price + categorical fields).
- Use active learning to surface uncertain items for future swipes.
- Rank new, unseen groceries and generate an HTML email with the best picks.
- The recommendation script runs after the weekly scrape as part of the GitHub Actions workflow.

Where in code:
- [scripts/recommender.py](scripts/recommender.py): ranking, recommendation, and email sending workflow.

## Data flow at a glance 🔁

1. Scrape weekly flyer data -> raw CSV + images
2. Process data -> cleaned features + processed CSV
3. Swipe app -> preference labels stored in SQLite
4. Recommender -> ranked items
5. Email -> weekly recommendations
