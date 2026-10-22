# Shortly - URL shortener on a DevOps platform

A URL shortener API built to practice a complete DevOps workflow: containers,
CI/CD, Kubernetes, GitOps and monitoring. The application is deliberately
simple; the focus is on everything built around it.

## Architecture

```
                 +--------------------+
   Client ------>|   API (Flask +     |
   (curl/browser)|   gunicorn)        |
                 +----+----------+----+
                      |          |
            cache miss|          |cache hit
                      v          v
             +-------------+  +-------------+
             | PostgreSQL  |  |    Redis    |
             | (links,     |  | (cached     |
             |  clicks)    |  |  redirects) |
             +------+------+  +-------------+
                    |
              volume db_data
              (persistent)
```

## Tech stack

| Area | Tools |
|---|---|
| API | Python, Flask, gunicorn |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Containers | Docker (multi-stage build), Docker Compose |
| Tests | pytest |
| Version control | Git, GitHub (SSH) |

## Quick start

Requirements: Docker with Docker Compose.

```
git clone git@github.com:jamili-meriem/devops-platform.git
cd devops-platform
docker compose up -d --build
curl http://localhost:5001/health
```

Create and use a short link:

```
curl -X POST http://localhost:5001/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.github.com"}'
curl -i http://localhost:5001/<code>
curl http://localhost:5001/stats/<code>
```

Stop everything: `docker compose down` (add `-v` to also delete the data).

## API

| Route | Description |
|---|---|
| `POST /shorten` | Create a short link from a JSON body `{"url": "..."}` |
| `GET /<code>` | Redirect to the original URL and count the click |
| `GET /stats/<code>` | Original URL and number of clicks |
| `GET /health` | Liveness check |

The `X-Cache` response header shows `HIT` (served from Redis) or `MISS`
(read from PostgreSQL).

## Tests

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r app/requirements-dev.txt
docker compose up -d db cache
cd app && pytest -v
```

## Design decisions

- **Configuration through environment variables** (`DATABASE_URL`,
  `REDIS_URL`, `CACHE_TTL`): the same image runs on any environment.
- **Multi-stage Dockerfile**: the final image only contains what is needed
  to run the application.
- **Non-root container user**: limits the impact of a vulnerability.
- **gunicorn instead of the Flask dev server**: suitable for production.
- **Healthchecks and `depends_on`**: the API starts only once PostgreSQL and
  Redis are ready.
- **Named volume** for PostgreSQL: data survives container recreation.
- **Resilient cache**: if Redis is down, the API keeps working by reading
  from PostgreSQL.
- **Parameterized SQL queries**: protection against SQL injection.

## Roadmap

- [x] Containerized application (Docker, Docker Compose)
- [ ] CI pipeline with GitHub Actions (tests, lint, security scan, image build)
- [ ] Kubernetes deployment (kind) and Helm chart
- [ ] GitOps with ArgoCD
- [ ] Monitoring with Prometheus and Grafana
- [ ] Infrastructure as code with Terraform
- [ ] Secrets management and security policies
