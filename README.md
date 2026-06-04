# snip. — URL Shortener

A clean, minimal URL shortener built with **FastAPI** + **SQLite**.

## Features
- Shorten any URL to a 6-character code
- Custom aliases (e.g. `/my-link`)
- Click tracking
- Stats page per link
- Recent links dashboard

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

## Project Structure

```
urlshortener/
├── main.py           # FastAPI app (routes, DB logic)
├── requirements.txt
├── templates/
│   ├── index.html    # Main page
│   └── stats.html    # Per-link stats page
└── urls.db           # SQLite database (auto-created on first run)
```

## API Endpoints

| Method | Path          | Description                        |
|--------|---------------|------------------------------------|
| GET    | `/`           | Homepage with shortener form       |
| POST   | `/shorten`    | Create a short URL                 |
| GET    | `/:code`      | Redirect to original URL (302)     |
| GET    | `/stats/:code`| View stats for a short URL         |

## How it works

1. User submits a long URL (+ optional custom alias)
2. Server generates a random 6-char alphanumeric code (or uses the custom one)
3. Mapping is saved to SQLite: `code → long_url`
4. On visit, server looks up the code and issues a `302` redirect
5. Each visit increments the click counter

## Extending ideas
- Add expiry dates (`expires_at` column)
- Add a password-protected admin dashboard
- Deploy to Railway / Render / Fly.io
- Add QR code generation
- Track more analytics (IP, referrer, browser)
