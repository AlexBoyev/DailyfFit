# DailyFit — Your Personal Training & Nutrition Platform 💪

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![MySQL 8.0](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![FastAPI 1.x](https://img.shields.io/badge/FastAPI-1.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏋️ Project Overview

**DailyFit** is a full-stack fitness application that lets users:

* generate **personalised workout programmes** and **nutrition menus**
* **book / cancel classes** and track attendance
* **chat with trainers** or AI (TinyLLaMA)
* **monitor progress** through live dashboards

Everything runs locally with Docker Compose — one command spins up the API, database, monitoring stack, and an LLM sandbox for experimentation.

---

## ✨ Key Features

| Domain            | What you get                                         |
| ----------------- | ---------------------------------------------------- |
| **Training**      | Goal-based plans (weight-loss, fitness, muscle gain) |
| **Nutrition**     | Auto-generated menus respecting allergies & macros   |
| **Scheduling**    | Class registration, cancellations & reminders        |
| **Admin**         | User / trainer management, reports & analytics       |
| **Chatbot**       | TinyLLaMA (via Ollama) answers health questions      |
| **Observability** | Prometheus metrics + pre-built Grafana dashboards    |
| **Security**      | JWT auth, RBAC, hashed passwords, Captcha            |

---

## 🔧 Tech Stack

| Layer          | Tech / Tooling                           |
| -------------- | ---------------------------------------- |
| **Backend**    | Python 3.11 · FastAPI · Uvicorn          |
| **Database**   | MySQL 8 (dockerised)                     |
| **Frontend**   | Jinja templates + static HTML/CSS        |
| **LLM**        | Ollama container running TinyLLaMA       |
| **Monitoring** | Prometheus v2 · Grafana                  |
| **DevOps**     | Docker Compose · .env config · GitHub CI |

---

## 🏗️ Repository Layout

```text
new-dailyFit/
├── backend/           ← FastAPI application (routers, services, models)
├── frontend/          ← HTML templates, CSS, images
├── monitoring/        ← Prometheus & Grafana provisioning and dashboards
├── sql/               ← Init scripts, seed data, migrations
├── tinyllama/         ← LLM utilities + prompt engineering helpers
├── docker-compose.yaml← Compose configuration for all services
├── startup.sh         ← Convenience script (build, up, health-check spinner)
├── .env.example       ← Copy → .env and fill secrets
└── README.md          ← Project overview and usage
```

---

## 🚀 Quick Start

1. **Clone & enter**:

   ```bash
   git clone https://github.com/AlexBoyev/DailyfFit.git
   cd DailyfFit
   ```

2. **Install Python dependencies** (if running locally outside Docker):

   ```bash
   pip install -r requirements.txt
   ```

3. **Create your `.env`** from the example:

   ```bash
   cp .env.example .env
   # Edit .env and set DB_USER, DB_PASSWORD, JWT_SECRET, etc.
   ```

4. **Launch the entire stack**:

   ```bash
   docker compose up -d --build
   ```

5. **Access the services**:

   * **API docs:**     `http://localhost:8000/docs`
   * **Frontend:**     `http://localhost:8000`
   * **Grafana:**      `http://localhost:3030`
   * **Prometheus:**   `http://localhost:9091/targets`
   * **Ollama API:**   `http://localhost:11434`

---

## ⚙️ Configuration

Copy `.env.example` → `.env` and set your values:

| Variable          | Purpose                          | Default                |
| ----------------- | -------------------------------- | ---------------------- |
| `DB_USER`         | MySQL username                   | `root`                 |
| `DB_PASSWORD`     | MySQL password                   | `yourpassword`         |
| `DB_NAME`         | Database name                    | `dailyfit`             |
| `JWT_SECRET`      | HS256 secret key                 | `change-me`            |
| `PROMETHEUS_PORT` | FastAPI metrics port             | `8001`                 |
| `GRAFANA_PORT`    | Host port for Grafana            | `3030`                 |
| `PROMETHEUS_HOST` | Prometheus container scrape host | `host.docker.internal` |
| `OLLAMA_MODEL`    | LLM model name                   | `tinyllama:latest`     |

---

## 📈 Monitoring Dashboards

* **Prometheus** auto-scrapes `/metrics` via `prometheus-fastapi-instrumentator`.
* **Grafana** is provisioned from `monitoring/grafana/datasources/` and imports all JSON under `monitoring/grafana/dashboards/` via `dashboards.yaml`.

Your pre-built dashboards include:

* **API Latency & Throughput**
* **MySQL Activity**
* **Docker Resource Usage**
* **TinyLLaMA Token Stats**

---

## 🧪 Testing

```bash
# Run pytest inside the backend container
docker compose exec backend pytest -q
```

CI will enforce formatting (black, ruff) and test coverage.

---

## 🤖 TinyLLaMA (via Ollama)

```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"tinyllama","prompt":"Give me a 3-day workout plan"}'
```

Your FastAPI `/chat` endpoint also integrates user data for personalized advice.

---

## 📝 License

Distributed under the **MIT License**. See `LICENSE` for details.
