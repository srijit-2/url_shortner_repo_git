import sqlite3, random, string, re
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).parent

DB = "urls.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                code        TEXT PRIMARY KEY,
                long_url    TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                click_count INTEGER DEFAULT 00N
            )
        """)
        conn.commit()

def gen_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

def is_valid_url(url: str) -> bool:
    pattern = re.compile(r'^https?://.+\..+')
    return bool(pattern.match(url))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with get_db() as conn:
        recent = conn.execute(
            "SELECT code, long_url, click_count, created_at FROM urls ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
    return templates.TemplateResponse("index.html", {"request": request, "recent": recent})


@app.post("/shorten", response_class=HTMLResponse)
async def shorten(request: Request, long_url: str = Form(...), custom_code: str = Form("")):
    long_url = long_url.strip()
    custom_code = custom_code.strip()

    if not long_url.startswith("http"):
        long_url = "https://" + long_url

    if not is_valid_url(long_url):
        return templates.TemplateResponse("index.html", {
            "request": request, "error": "Please enter a valid URL.", "recent": []
        })

    with get_db() as conn:
        # Use custom code or generate one
        code = custom_code if custom_code else None
        if code:
            if not re.match(r'^[a-zA-Z0-9_-]+$', code):
                return templates.TemplateResponse("index.html", {
                    "request": request, "error": "Custom alias can only contain letters, numbers, - and _.", "recent": []
                })
            existing = conn.execute("SELECT code FROM urls WHERE code = ?", (code,)).fetchone()
            if existing:
                return templates.TemplateResponse("index.html", {
                    "request": request, "error": f"Alias '{code}' is already taken.", "recent": []
                })
        else:
            for _ in range(10):
                code = gen_code()
                if not conn.execute("SELECT code FROM urls WHERE code = ?", (code,)).fetchone():
                    break

        conn.execute(
            "INSERT INTO urls (code, long_url, created_at) VALUES (?, ?, ?)",
            (code, long_url, datetime.utcnow().isoformat())
        )
        conn.commit()

        short_url = str(request.base_url) + code
        recent = conn.execute(
            "SELECT code, long_url, click_count, created_at FROM urls ORDER BY created_at DESC LIMIT 5"
        ).fetchall()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "short_url": short_url,
        "code": code,
        "original": long_url,
        "recent": recent
    })


@app.get("/stats/{code}", response_class=HTMLResponse)
async def stats(request: Request, code: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM urls WHERE code = ?", (code,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return templates.TemplateResponse("stats.html", {"request": request, "row": row})


@app.get("/{code}")
async def redirect(code: str):
    with get_db() as conn:
        row = conn.execute("SELECT long_url FROM urls WHERE code = ?", (code,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Short URL not found")
        conn.execute("UPDATE urls SET click_count = click_count + 1 WHERE code = ?", (code,))
        conn.commit()
    return RedirectResponse(url=row["long_url"], status_code=302)
