# Module 3 — AI Vision Refund Verification

*Zepto Smart Commerce AI Platform — this project builds Module 3 only,
against the official spec's "AI Vision Refund Verification" section, its
shared 6-table database schema, and the **Zepto Refund and Damaged Goods
Policy (v4.1)** (`data/policies/02_refund_policy.pdf`). Module 3's own spec
sheet lists its tech as Gemini Vision API + AWS S3 + Prompt Engineering —
no separate API framework — so this project is deliberately just Python +
PostgreSQL/SQLite + Streamlit: a notebook, one SQL file, one `src/` package,
one dashboard script. Nothing extra.*

A customer says the milk packet was leaking. Instead of a human agent opening
the photo and guessing, Gemini Vision looks at the image, identifies the
product, describes the damage, gives a confidence score, and a refund engine
applies the policy's business rules to auto-approve, escalate, or reject the
claim.

This project is a working, end-to-end implementation of the pipeline:
**upload → S3-style storage → Gemini Vision → JSON parsing/validation →
policy-driven rules engine → PostgreSQL `refund_claims` record → Streamlit
dashboard.**

## Everything here is real data — nothing mocked or sampled

- **Users, orders, order items**: loaded from the actual Zepto dataset
  provided with this capstone (`data/processed/*.parquet`,
  `data/catalogue/*.csv`) — not self-seeded demo rows. See "Real data"
  below for exactly how.
- **Damage photos**: this project bundles **none**. The provided dataset
  has real orders, reviews, and a product catalogue, but no images at all
  — so there was nothing to bundle, and nothing was faked to fill the gap.
  Upload a real photo through the dashboard to run the vision step for
  real. See "About the photo step" below.
- **Vision model**: defaults to real Gemini Vision (`VISION_BACKEND=gemini`)
  — set one free API key and it's live. There's an explicit opt-in
  `VISION_BACKEND=offline` fallback with no network calls for trying the
  rest of the pipeline without a key, but it's not the default and isn't
  what the notebook demonstrates.

## Real data, not synthetic demo rows

`src/data_loader.py` loads real users, orders, and order line-items
straight from the Zepto dataset provided with this capstone:

```
data/
  processed/orders_clean.parquet    real Module 1 delivery dataset (~80k rows)
  processed/reviews_clean.parquet   real Module 2 reviews dataset (~8k rows)
  catalogue/products.csv            real product catalogue (name, category, price, ...)
```

The orders dataset alone has no customer or line-item columns at all (it was
built for Module 1's delivery-time prediction). The only real link from an
order to *who bought it* and *what they bought* is through the reviews
dataset (`order_id -> user_id, product_id`). So `db.load_real_data_if_needed()`
loads the ~4.8k real, delivered orders that have a resolvable real customer
**and** real product via that link — every order_amount, delivery time,
store, product name, category, and price you'll see in this project is
real data, not invented. `src/data_loader.py`'s module docstring spells out
exactly what's real vs. derived for every field (e.g. `delivered_at` is
computed from two real columns; `id`/`user_id` are UUIDs deterministically
derived from the real string IDs, kept in `source_order_id`/`source_user_id`,
because the platform schema requires UUID FKs but the dataset's IDs aren't
valid UUIDs). Controlled by `DATA_DIR` and `DATA_LOAD_LIMIT` in `.env`.

## About the photo step

Module 3's entire premise is a vision model looking at a damage photo — but
the provided dataset has no photographs of anything. Rather than generate
placeholder images to paper over that, this project doesn't bundle any: the
notebook's vision cells explain the step and skip cleanly when no photo is
given, and the dashboard's file uploader is the real way to test it — pick
a real order, upload any real photo, and Gemini Vision analyses it for real.

## Scope: Module 3 only

The full platform is 5 modules sharing one PostgreSQL database. This project
builds Module 3. `schema.sql` includes the platform's complete 6-table
schema (per the spec's "Database: PostgreSQL schema created with all six
required tables" deliverable), but only a few tables are actively used here:

- **`users`, `orders`** — prerequisite tables, populated with **real** rows
  (see above) rather than synthetic demo data. `refund_claims.order_id` is a
  real foreign key into `orders`.
- **`refund_claims`** — Module 3's actual output table. Column names and
  types match the spec exactly (`id` UUID, `order_id` FK, `product_name`,
  `damage_type`, `damage_description`, `image_s3_key`, `vision_confidence`
  0-1, `decision`, `refund_amount`, `created_at`) so Modules 4 and 5, which
  read this table directly per the spec, can consume it unchanged.
- `delivery_predictions`, `reviews`, `chat_logs` (Modules 1/2/4 outputs) are
  included as empty tables only so the full shared schema is present — this
  project doesn't write to them.
- `refund_thresholds`, `order_items` are **not** part of the platform's
  6-table schema — this project's own additions. `refund_thresholds` because
  the spec requires configurable (not hardcoded) confidence thresholds;
  `order_items` because the refund policy's "claimed product matches an item
  on the order" rule (REF-3.1) and partial refunds (REF-4.3) need real
  per-order product data that the platform schema doesn't otherwise carry.
  `users`/`orders` also carry a `source_user_id`/`source_order_id` column —
  same reasoning, see "Real data" above.

## What's in here

```
module3_refund_verification.ipynb   Full walkthrough, already executed
schema.sql                           Full platform schema (see "Scope" above)
src/                                  Core pipeline package
  config.py            All settings, env-var driven
  data_loader.py         Loads real users/orders/order_items from data/ — see its docstring
  storage.py            S3-style storage (local folder by default, real boto3 S3 backend included)
  image_preprocessing.py Resize / compress / strip EXIF (Pillow + OpenCV)
  vision.py              Structured-JSON prompt, Gemini (default) + offline-fallback backends
  rules_engine.py         REF v4.1 policy rules -> decision + reason code, thresholds never hardcoded
  db.py                   SQLAlchemy models (6 platform tables + order_items + refund_thresholds), Postgres or SQLite
  pipeline.py              Orchestrates all of the above (used by the notebook and dashboard)
dashboard.py                          Streamlit ops dashboard
requirements.txt
.env.example
```

`data/` isn't part of this deliverable — it's the dataset you already have
alongside this project; nothing here modifies it.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Then set GEMINI_API_KEY in .env — the only thing you actually need to
# fill in. Get a free key at https://aistudio.google.com/apikey.
```

Make sure `data/processed/*.parquet` and `data/catalogue/*.csv` are present
(they should already be, alongside this README) — that's where the real
users/orders/products come from.

**Run the notebook** (already executed once and saved with outputs, so you
can also just open and read it):
```bash
jupyter notebook module3_refund_verification.ipynb
```

**Run the dashboard:**
```bash
streamlit run dashboard.py
```

Both share the same `src/` pipeline and the same database, so a claim
submitted in the dashboard shows up in the notebook's queries and vice versa.
On first run, `db.load_real_data_if_needed()` loads real orders automatically
(capped at `DATA_LOAD_LIMIT`, default 2000, most recent first) — the
dashboard's "Submit a claim" tab lets you pick one from a dropdown, and shows
the order's real item(s) alongside it.

## Troubleshooting: `ArrowKeyError: A type extension with name pandas.period already defined`

This can show up when running the notebook (usually on the `load_real_data_if_needed()`
cell) in VS Code / Jupyter on Windows. It's pyarrow registering its
pandas.period extension type twice inside one Python process — caused by
having more than one pyarrow install on the interpreter's path (commonly:
VS Code's selected Jupyter kernel isn't the same venv where you ran
`pip install -r requirements.txt`, so it's picking up a second, older
pyarrow from elsewhere). It is not a bug in this project's logic — every
verification run here (SQLite and Postgres) uses a single clean pyarrow
install and never hits it.

Two ways out, and you don't have to choose — do both:

1. **`src/data_loader.py` already works around it.** `_read_parquet_resilient()`
   catches exactly this error and retries the read with the `fastparquet`
   engine (no pyarrow involved at all), which is in `requirements.txt`.
   So a plain `pip install -r requirements.txt` followed by a full kernel
   **restart** (not just re-running the one cell) should let it through.
2. **Fix the underlying duplicate install**, so pyarrow itself is healthy:
   check `python -c "import sys; print(sys.executable)"` and `pip show
   pyarrow` *inside the same kernel VS Code is using* for the notebook, and
   confirm that's the venv you installed `requirements.txt` into. If it's a
   different Python, switch the notebook's kernel (top-right kernel picker
   in VS Code) to the right one and restart it.

## Connecting to your real PostgreSQL instance

1. Set `DATABASE_URL` (in `.env` or your shell) to your instance, e.g.
   ```
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```
2. Apply the schema once:
   ```bash
   psql "$DATABASE_URL" -f schema.sql
   ```
   Real data loads automatically on first notebook/dashboard run — there's
   no separate seed file to run.
3. That's it — `src/db.py` reads `DATABASE_URL` automatically; the notebook
   and dashboard both pick it up with no code changes.

This was re-verified end-to-end against a real local PostgreSQL 16 instance
after this rebuild: schema apply, the real-data load (~2000 orders + their
order_items), full pipeline writes (auto-approval, the UUID foreign keys,
and the `payment_status` update), and Streamlit all confirmed working
against real Postgres, not just SQLite. One Postgres-only fix was needed
along the way: SQLAlchemy 2.0's bulk-insert optimization doesn't tolerate
psycopg2's native-UUID auto-casting on a client-supplied `String(36)` PK
column, so it's disabled for non-SQLite engines in `src/db.py` (see the
comment there) — real-data loads fall back to one INSERT per row, still a
couple of seconds for a few thousand rows.

## Vision: Gemini by default

`VISION_BACKEND=gemini` is the default — set `GEMINI_API_KEY` in `.env`
(free tier, get one at https://aistudio.google.com/apikey) and that's the
only setup required. If it's unset, `analyse_damage()` fails immediately
with a clear message rather than silently falling back to anything.

If you want to exercise the rest of the pipeline (storage, rules engine,
database, dashboard) without a key handy, set `VISION_BACKEND=offline` — a
deterministic, no-network stand-in. It's an explicit opt-in, not the
default, and isn't what this project demonstrates as its real vision step
(`src/vision.py`'s docstring explains it fully).

## Switching on real AWS S3

By default `STORAGE_BACKEND=local` — photos are written to `./refunds/` in
the exact same `refunds/{user_id}/{claim_id}/{filename}` layout a real S3
bucket would use.

To use real S3:
```
STORAGE_BACKEND=s3
S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
```
Plus the standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars (or
an IAM role) — `src/storage.py::S3Storage` handles the rest via `boto3`.

## Business rules — REF v4.1

`src/rules_engine.py::decide()` implements the refund policy PDF
(`data/policies/02_refund_policy.pdf`), not just a confidence threshold.
Auto-approval (REF-3.1) requires **all** of:

| Check | Policy ref |
|---|---|
| Vision confidence above the auto-approve threshold | REF-3.1 |
| The claimed product matches a real item on the order (`order_items`) | REF-3.1 |
| No fraud indicator — fewer than `FRAUD_CLAIM_COUNT_THRESHOLD` claims from this account in the last `FRAUD_LOOKBACK_DAYS` days | REF-3.1 / REF-5.1 |
| Refund value within the auto-approval cap (`AUTO_APPROVE_REFUND_CAP`, default Rs 500) | REF-3.1 |
| Filed within the eligibility window from delivery | REF-1.1 / REF-1.2 / REF-1.3 |
| A usable photo was submitted | REF-2.1 |

Eligibility windows (REF-1.1/1.2/1.3): **2 hours** for perishables
(vegetables, fruits, milk and dairy, eggs, frozen foods), **24 hours** for
packaged goods (packaged groceries, beverages, snacks, household products)
and for missing/wrong-item claims regardless of category. Missing a usable
photo routes to `manual_review`, **not** an outright rejection (REF-2.1) —
same for a photo the vision model couldn't parse at all. Failing any other
auto-approval precondition with a strong-enough photo also routes to
`manual_review` (a human can still approve it); only low confidence or a
claim outside its window is rejected outright.

Every decision carries a specific **reason code** (REF-3.5) — e.g.
`outside_eligibility_window`, `product_not_on_order`, `fraud_indicator`,
`over_auto_approve_cap`, `medium_confidence` — with a matching customer-
facing message in `rules_engine.REASON_MESSAGES`, shown in the dashboard.

**Confidence thresholds** are **not hardcoded** — they live in the
`refund_thresholds` table and are read fresh at decision time
(`src/db.py::get_active_thresholds`), so operations can tighten them during
a fraud spike with no redeploy. Edit them live from the Streamlit
dashboard's "Thresholds" tab, or directly:
```python
from src import db
db.set_active_thresholds(auto_approve_min=99, manual_review_min=85, updated_by="ops")
```
The Rs 500 cap, the eligibility windows, and the fraud-indicator threshold
are env-var configurable too (`.env.example`) but aren't day-to-day tuning
knobs the way confidence thresholds are, so they're not exposed for live
editing in the dashboard — just shown there for visibility.

On auto-approval, `refund_amount` is the **matched item's real price**
(REF-4.3 — a partial refund, not automatically the whole order) and the
order's `payment_status` is set to `'refunded'`, simulating the payment-
reversal queue. On manual review, `refund_amount` is left `NULL` pending a
human decision; on rejection it's `0`.

### Why "now" is simulated for eligibility windows

The real dataset is a static historical snapshot (Jan-Jun 2026). Comparing
an order's `delivered_at` to true wall-clock time would put every real order
weeks or months outside even the 24h window, regardless of anything else —
useless for demoing the pipeline. `db.get_window_reference_now()` instead
uses the most recent `delivered_at` among the orders actually loaded as
"now" — i.e. "pretend today is the last day this dataset covers" — so which
claims fall inside vs. outside their window still depends on real, varying
delivery timestamps, not a hardcoded date. This only affects the eligibility-
window check; the fraud-indicator lookback (REF-5.1) uses true wall-clock
time against `refund_claims.created_at`, since claims *this project writes*
are always timestamped for real.

## Damage & product categories

**Damage:** broken, cracked, leaking, expired, rotten, spoiled, missing item,
wrong product, torn package, opened package, wet packaging, crushed product.

**Products:** vegetables, fruits, milk and dairy, eggs, snacks, packaged
groceries, beverages, frozen foods, household products — the same 9
categories used in the real product catalogue (`data/catalogue/products.csv`).

Both lists are enforced by the JSON schema in `src/vision.py` — a vision
response outside these categories fails validation and triggers a retry.

## Notes on what's real vs. what needs your setup

- **Data**: users, orders, and order_items are real (see "Real data" above)
  — nothing in the database is fabricated except the deterministic UUID
  mapping the platform schema's FK columns require (original IDs kept in
  `source_user_id`/`source_order_id`).
- **Vision**: real Gemini Vision by default — the only thing you need to
  add is a free API key (see "Vision: Gemini by default" above). No photo
  is bundled with the project; upload your own through the dashboard.
- **Storage**: local-folder stand-in by default, with a real `boto3` S3
  backend included but not exercised against an actual AWS account. Only
  the first (primary) photo of a claim is analysed and its key stored in
  `refund_claims.image_s3_key` (a single column, per the spec's schema);
  any additional photos (up to 3 are accepted) are still uploaded under the
  same claim prefix for a human reviewer to open.
- **Database**: the full schema and pipeline — including the UUID foreign
  keys, the CHECK-constrained `decision` column, the real-data bulk load,
  and the `payment_status` update — were verified against a real local
  PostgreSQL 16 instance. Point `DATABASE_URL` at your own instance and
  re-run `schema.sql` there — no other changes needed.
