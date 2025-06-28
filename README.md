# DailyFit — Your Personal Training & Nutrition Platform 💪

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![MySQL 8.0](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![FastAPI 1.x](https://img.shields.io/badge/FastAPI-1.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏋️ Project Overview

**DailyFit** is a full-stack fitness application that lets users

* generate **personalised workout programmes** and **nutrition menus**
* **book / cancel classes** and track attendance
* **chat with trainers** or AI (TinyLLaMA)
* **monitor progress** through live dashboards

Everything runs locally with Docker Compose — one command spins up the API, database, monitoring stack, and an LLM sandbox for experimentation.

---

## ✨ Key Features

| Domain        | What you get                                                         |
| ------------- | -------------------------------------------------------------------- |
| **Training**  | Goal-based plans (weight-loss, fitness, muscle gain)                 |
| **Nutrition** | Auto-generated menus respecting allergies & macros                   |
| **Scheduling**| Class registration, cancellations & reminders                        |
| **Admin**     | User / trainer management, reports & analytics                       |
| **Chatbot**   | TinyLLaMA (via Ollama) answers health questions                      |
| **Observability** | Prometheus metrics + pre-built Grafana dashboards               |
| **Security**  | JWT auth, RBAC, hashed passwords                                     |

---

## 🔧 Tech Stack

| Layer         | Tech / Tooling                                   |
| ------------- | ------------------------------------------------ |
| **Backend**   | Python 3.11 · FastAPI · Uvicorn                  |
| **Database**  | MySQL 8 (dockerised)                             |
| **Frontend**  | Jinja templates + static HTML/CSS (placeholder)  |
| **LLM**       | Ollama container running TinyLLaMA 3B            |
| **Monitoring**| Prometheus v2 · Grafana 10 (auto-provisioned)    |
| **Dev Ops**   | Docker Compose · .env config · GitHub CI         |

---

## 🏗️ Repository Layout

```text
DailyFit/
├── backend/           ← FastAPI application (routers, services, models)
├── frontend/          ← HTML templates, CSS, images
├── monitoring/
│   ├── grafana/       ← Provisioning & dashboards
│   └── prometheus/    ← prometheus.yml & rules
├── sql/               ← Init.sql, seed scripts, migrations
├── tinyllama/         ← LLM utilities + prompt engineering helpers
├── docker-compose.yaml
├── startup.sh         ← Convenience script (build + up)
├── .env.example       ← Copy → .env and fill secrets
└── README.md
```

---

## 🚀 Quick Start

```bash
# 1) Clone & enter
git clone https://github.com/<you>/DailyFit.git
cd DailyFit

# 2) Copy env template and tweak ports / secrets
cp .env.example .env
nano .env            # or favourite editor

# 3) Launch the entire stack
docker compose up -d --build

# 4) Open browser:
#    • API docs:       http://localhost:8000/docs
#    • Frontend:       http://localhost:8000
#    • Grafana:        http://localhost:3000  (admin / admin)
#    • Prometheus:     http://localhost:9090
#    • TinyLLaMA chat: http://localhost:11434  (Ollama HTTP API)
```

> **Tip:** `startup.sh` wraps the same command with log-follow and a health-check spinner.

---

## ⚙️ Configuration

| Variable          | Purpose                               | Default              |
| ----------------- | ------------------------------------- | -------------------- |
| `DB_USER`         | MySQL username                        | `dailyfit`           |
| `DB_PASS`         | MySQL password                        | `dailyfit`           |
| `DB_NAME`         | Database name                         | `dailyfit`           |
| `JWT_SECRET`      | HS256 secret key                      | change-me            |
| `PROMETHEUS_PORT` | Prometheus scrape endpoint (backend)  | `8000/metrics`       |
| `OLLAMA_MODEL`    | LLM model name                        | `tinyllama:latest`   |

Edit **`.env`** to override anything at run-time.

---

## 📈 Monitoring Dashboards

* **Prometheus** automatically scrapes FastAPI via [`prometheus-fastapi-instrumentator`](https://github.com/trallnag/prometheus-fastapi-instrumentator).
* **Grafana** is pre-configured with:
  * **API Latency & Throughput**
  * **MySQL Queries / Connections**
  * **Docker Resources**
  * **LLM Usage & Token stats**

Dashboards live in `monitoring/grafana/dashboards/` and are auto-imported on first run.

---

## 🧪 Testing

```bash
# run pytest unit + integration tests
docker compose exec backend pytest -q
```

CI will fail on merge requests if tests or formatting (ruff / black) break.

---

## 🤖 TinyLLaMA Usage

```bash
curl -s -X POST http://localhost:11434/api/generate   -d '{"model":"tinyllama", "prompt":"Give me a 3-day workout plan"}'
```

The backend exposes `/chat` which pipes authenticated user data (nutrition logs, weight history) into TinyLLaMA for personalised advice.


* WebSocket live-class streaming  

---

## 📝 License

Distributed under the **MIT License**. See `LICENSE` for details.

