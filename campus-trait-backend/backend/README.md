# Campus Trait API

A real Python backend for the Campus Trait marketplace, built with **FastAPI** +
**SQLAlchemy** + **SQLite**. It implements everything the frontend needs:
authentication, listings (search/filter/sort), image uploads, wishlist,
conversations/messaging, and profile/dashboard stats.

## Quick start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**, with interactive
docs (Swagger UI) at **http://localhost:8000/docs**.

On first run it automatically creates `campus_trait.db` (SQLite file) and
seeds it with demo users, listings, and one sample conversation so there's
data to explore immediately.

### Demo accounts

Every seeded user shares the password `password123`. The main demo account
(matching "Aarav Sharma" in the frontend) is:

```
email:    aarav@campustrait.edu
password: password123
```

## Project layout

```
backend/
  app/
    main.py          # FastAPI app, CORS, static file mount, startup seed
    database.py       # SQLAlchemy engine/session
    models.py         # ORM models: User, Item, ItemImage, Wishlist, Conversation, Message
    schemas.py         # Pydantic request/response schemas
    security.py        # password hashing (pbkdf2_sha256) + JWT
    deps.py            # get_db / get_current_user dependencies
    utils.py            # saves base64 image uploads to /uploads
    seed.py              # demo data matching the frontend mockups
    routers/
      auth.py            # register, login, /me
      items.py            # browse/search/filter/sort, CRUD, categories
      wishlist.py          # add/remove/toggle/list
      messages.py           # conversations + messages
      users.py               # dashboard stats, public profile
  requirements.txt
  uploads/               # uploaded listing photos land here (served at /uploads/*)
```

## Authentication

Standard OAuth2 "password flow", JWT bearer tokens.

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@campustrait.edu","password":"secret123"}'

# Login (form-encoded, "username" field carries the email — this is what
# lets Swagger's "Authorize" button work out of the box)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=jane@campustrait.edu&password=secret123"

# Use the returned access_token on every authenticated request:
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer <token>"
```

## Key endpoints

| Method | Path                                | Auth?   | Description |
|--------|--------------------------------------|---------|--------------|
| POST   | `/api/auth/register`                | No      | Create an account |
| POST   | `/api/auth/login`                   | No      | Get a JWT access token |
| GET    | `/api/auth/me`                      | Yes     | Current user |
| GET    | `/api/items`                        | Optional| Browse/search/filter/sort listings |
| GET    | `/api/items/{id}`                   | Optional| Listing detail |
| POST   | `/api/items`                        | Yes     | Create a listing (images as base64 data URIs or hosted URLs) |
| PATCH  | `/api/items/{id}`                   | Yes     | Edit / mark sold / move to draft (owner only) |
| DELETE | `/api/items/{id}`                   | Yes     | Delete a listing (owner only) |
| GET    | `/api/items/meta/categories`        | No      | Category list |
| GET    | `/api/wishlist`                     | Yes     | Your wishlisted items |
| POST   | `/api/wishlist/{item_id}/toggle`    | Yes     | Add/remove in one call (what the UI's heart button uses) |
| GET    | `/api/conversations`                | Yes     | Your conversations, with unread counts |
| POST   | `/api/conversations`                | Yes     | Start a conversation about an item |
| GET    | `/api/conversations/{id}`           | Yes     | Full thread (marks messages read) |
| POST   | `/api/conversations/{id}/messages`  | Yes     | Send a message |
| GET    | `/api/users/me/dashboard`           | Yes     | Active / sold / draft counts for the seller dashboard |

`GET /api/items` query params: `search`, `category`, `sort` (`recent`\|`low`\|`high`),
`status` (`active`\|`sold`\|`draft`\|`all`), `mine` (bool), `limit`, `offset`.

### Uploading photos

The frontend's sell-flow reads photos into base64 via `FileReader` in the
browser. Send them straight through as `image_urls` on `POST /api/items`:

```json
{
  "title": "Casio Scientific Calculator",
  "price": 700,
  "category": "calculators",
  "condition": "Good condition",
  "image_urls": ["data:image/png;base64,iVBORw0KG..."]
}
```

The server decodes each one, writes it to `uploads/`, and stores the URL
(`/uploads/<file>.png`) on the listing. Already-hosted `http(s)://` URLs are
passed through unchanged, so seed/demo data can also just link an image.

## Connecting the existing frontend

The `campus-trait.html` frontend currently runs entirely on in-memory mock
data. To wire it up to this API: replace the mock `items`/`conversations`
arrays and direct state mutations with `fetch()` calls to the endpoints
above, store the JWT (in memory — no `localStorage`, per the artifact's
constraints) after login, and send it as `Authorization: Bearer <token>` on
every request. Happy to do that wiring next if you'd like — just ask.

## Configuration

Both are optional environment variables with sane defaults:

- `DATABASE_URL` — defaults to a local SQLite file. Point it at Postgres/MySQL
  in production, e.g. `postgresql://user:pass@host/dbname`.
- `SECRET_KEY` — JWT signing secret. **Set a real one before deploying.**

## Notes

- Passwords are hashed with `pbkdf2_sha256` (via passlib) — no native
  compiled dependency required, unlike bcrypt.
- CORS is wide open (`allow_origins=["*"]`) for easy local development;
  restrict this to your actual frontend origin before deploying.
