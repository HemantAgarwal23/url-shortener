# URL Shortener API

A clean, beginner-friendly URL shortener backend built with FastAPI and SQLite.
It supports creating short links, redirecting to original URLs, and tracking
basic metadata such as clicks and creation time.

## Project overview

This project provides a minimal REST API for URL shortening with:

- Base62 short code generation
- SQLite persistence
- Click tracking
- Created timestamp storage
- Structured JSON error handling

The codebase is modular and readable:

- `main.py` - API routes, logging, and error handlers
- `database.py` - SQLite setup and query functions
- `models.py` - Request and response models
- `utils.py` - URL validation and Base62 helpers
- `requirements.txt` - Dependencies

## Features

- Shorten long URLs using `POST /shorten`
- Reuse existing short code for duplicate long URLs
- Redirect via `GET /{code}`
- Track `click_count` on every redirect
- List all URLs via `GET /urls`
- Store `created_at` timestamp per URL
- Return structured JSON errors
- Basic request logging at INFO level

## Architecture

```mermaid
flowchart LR
    C[Client] -->|POST /shorten| A[FastAPI App]
    C -->|GET /urls| A
    C -->|GET /{code}| A
    A --> U[utils.py<br/>Validation + Base62]
    A --> D[database.py<br/>SQLite queries]
    D --> S[(SQLite DB)]
```

### Architecture Notes

The FastAPI app receives incoming requests and routes them to the correct handler.
Validation and short-code generation are handled in `utils.py`, while persistence is handled in `database.py`.
SQLite stores all URL records, including `short_code`, `click_count`, and `created_at`.

## Tech stack

- Python
- FastAPI
- SQLite
- Pydantic
- Uvicorn

## Endpoints with examples

### `POST /shorten`

Create a short URL from a long URL.
If the URL already exists, returns the existing short code gracefully.

Request:

```json
{
  "long_url": "https://example.com/some/very/long/path",
  "custom_code": "myLink123"
}
```

Response:

```json
{
  "long_url": "https://example.com/some/very/long/path",
  "short_code": "a1B2c3",
  "short_url": "http://localhost:8000/a1B2c3",
  "click_count": 0,
  "created_at": "2026-04-27 12:20:34"
}
```

### `GET /urls`

Return all stored URL records.

Response:

```json
{
  "urls": [
    {
      "long_url": "https://example.com/some/very/long/path",
      "short_code": "a1B2c3",
      "click_count": 2,
      "created_at": "2026-04-27 12:20:34"
    }
  ]
}
```

### `GET /{code}`

Redirect to the original URL for a given short code.

- Success: `307 Temporary Redirect`
- Not found: `404 Not Found`

## Sample request and response

Example using `curl`:

```bash
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d "{\"long_url\":\"https://fastapi.tiangolo.com/tutorial/\"}"
```

Sample response:

```json
{
  "long_url": "https://fastapi.tiangolo.com/tutorial/",
  "short_code": "0aZ91x",
  "short_url": "http://localhost:8000/0aZ91x",
  "click_count": 0,
  "created_at": "2026-04-27 12:35:12"
}
```

Error response format:

```json
{
  "error": {
    "code": "INVALID_URL",
    "message": "Invalid URL. Use a full http(s) URL like https://example.com"
  }
}
```

If `custom_code` is already used, the API returns:

- Status: `409 Conflict`
- Code: `CUSTOM_CODE_ALREADY_EXISTS`

## How to run locally

1. (Optional) Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the server:

```bash
uvicorn main:app --reload
```

4. Open:

- API docs: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Design Decisions

- Base62 for compact, URL-safe codes
- SQLite with indexed lookups for fast retrieval
- Collision handling via uniqueness checks
