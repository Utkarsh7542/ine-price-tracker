# INE Price Tracker

A small full-stack app that tracks prices and stock for products on INE's mock
store (https://demo.inelabteamdev.com). You search for a product, pick an
option, and it scrapes the price on a schedule so you can watch it move over
time.

The store makes scraping hard on purpose, and getting past that reliably was
most of the work. The price only loads after you hover the price box, it's
guarded by a puzzle that fails at random, and the number on the page is
surrounded by fake prices and invisible characters. How I dealt with all of
that is in DESIGN_NOTE.md.

## Live links
- App: https://ine-price-tracker-lyart.vercel.app/
- API: https://ine-price-tracker-jqoc.onrender.com
- Repo: https://github.com/Utkarsh7542/ine-price-tracker

## How it fits together
- Scraper (Playwright): opens the product in a real browser, gets past the guard, reads the price.
- GitHub Actions: runs the scraper every 2 hours. This is the schedule.
- Supabase (Postgres): stores tracked products and every scrape attempt.
- Backend (Django on Render): the API the dashboard reads from, plus CSV export.
- Frontend (React on Vercel): search, track, price chart, scrape log.

## The scraping schedule
GitHub Actions runs `.github/workflows/scrape.yml` on a cron of `0 */2 * * *`,
so every 2 hours (UTC). Each run scrapes every tracked product once and writes a
row to Supabase, whether it succeeded, needed retries, or failed. The dashboard
also has a "Scrape now" button that fires a run on demand.

## Run it locally
You need Python 3.11 and Node 18+.

Backend and scraper:
1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. Copy `.env.example` to `.env` and fill in your Supabase URL and key.
4. Set up the database (below).
5. `python run_scrapes.py` scrapes all tracked products once.
6. `python manage.py runserver` runs the API on http://localhost:8000.

Frontend:
1. `cd frontend`
2. `npm install`
3. `npm run dev` runs it on http://localhost:5173.

## Database setup
Run this in the Supabase SQL editor:

```sql
create table tracked_products (
  id            bigserial primary key,
  store_item_id integer not null,
  name          text not null,
  option_label  text not null,
  created_at    timestamptz not null default now(),
  unique (store_item_id, option_label)
);

create table scrape_log (
  id         bigserial primary key,
  product_id bigint not null references tracked_products(id) on delete cascade,
  scraped_at timestamptz not null default now(),
  outcome    text not null,
  price      numeric,
  mrp        numeric,
  stock      integer,
  currency   text,
  tries      integer not null default 1
);
create index scrape_log_by_product on scrape_log (product_id, scraped_at desc);

create table catalog (
  id       integer primary key,
  name     text not null,
  brand    text,
  category text
);

alter table tracked_products disable row level security;
alter table scrape_log disable row level security;
alter table catalog disable row level security;
```

Then `python seed_products.py` adds a few products to track, and
`python build_catalog.py` fills the catalog table so search works.

## Environment variables
Backend (`.env` locally, or set in Render):
- `SUPABASE_URL` your Supabase project URL
- `SUPABASE_KEY` your Supabase service_role key
- `GITHUB_TOKEN` a fine-grained token with Actions read/write, used by the "Scrape now" button
- `GITHUB_REPO` optional, defaults to `Utkarsh7542/ine-price-tracker`
- `SECRET_KEY` Django secret, any random string

GitHub Actions secrets (repo settings):
- `SUPABASE_URL`
- `SUPABASE_KEY`

Frontend (Vercel):
- `VITE_API_URL` optional, the backend URL. Defaults to the deployed Render URL.

## Watching it run
`python scraper.py` opens a visible browser and scrapes a few products so you
can watch it work, including the retries when the guard fails. The scheduled job
runs the same code with the browser hidden.
