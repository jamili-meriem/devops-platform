import os
import random
import string

import psycopg
import redis
from flask import Flask, jsonify, redirect, request

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://shortly:shortly_pass@localhost:5432/shortly",
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.environ.get("CACHE_TTL", "3600"))

cache = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_conn():
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


init_db()


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url or not url.startswith(("http://", "https://")):
        return jsonify(error="URL invalide"), 400
    for _ in range(5):
        code = generate_code()
        with get_conn() as conn:
            row = conn.execute(
                "INSERT INTO links (code, url) VALUES (%s, %s) "
                "ON CONFLICT (code) DO NOTHING RETURNING code",
                (code, url),
            ).fetchone()
        if row:
            return jsonify(code=code, short_url=f"{request.host_url}{code}"), 201
    return jsonify(error="Impossible de générer un code"), 500


@app.route("/<code>")
def go(code):
    try:
        url = cache.get(f"url:{code}")
        if url:
            cache.incr(f"clicks:{code}")
            resp = redirect(url, code=302)
            resp.headers["X-Cache"] = "HIT"
            return resp
    except redis.RedisError:
        pass

    with get_conn() as conn:
        row = conn.execute(
            "UPDATE links SET clicks = clicks + 1 WHERE code = %s RETURNING url",
            (code,),
        ).fetchone()
    if row is None:
        return jsonify(error="Lien introuvable"), 404

    try:
        cache.set(f"url:{code}", row[0], ex=CACHE_TTL)
    except redis.RedisError:
        pass
    resp = redirect(row[0], code=302)
    resp.headers["X-Cache"] = "MISS"
    return resp


@app.route("/stats/<code>")
def stats(code):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT url, clicks FROM links WHERE code = %s", (code,)
        ).fetchone()
    if row is None:
        return jsonify(error="Lien introuvable"), 404
    pending = 0
    try:
        pending = int(cache.get(f"clicks:{code}") or 0)
    except redis.RedisError:
        pass
    return jsonify(code=code, url=row[0], clicks=row[1] + pending)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
