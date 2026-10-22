import random
import string

from flask import Flask, jsonify, redirect, request

app = Flask(__name__)

links = {}


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
    code = generate_code()
    while code in links:
        code = generate_code()
    links[code] = {"url": url, "clicks": 0}
    return jsonify(code=code, short_url=f"{request.host_url}{code}"), 201


@app.route("/<code>")
def go(code):
    link = links.get(code)
    if link is None:
        return jsonify(error="Lien introuvable"), 404
    link["clicks"] += 1
    return redirect(link["url"], code=302)


@app.route("/stats/<code>")
def stats(code):
    link = links.get(code)
    if link is None:
        return jsonify(error="Lien introuvable"), 404
    return jsonify(code=code, url=link["url"], clicks=link["clicks"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
