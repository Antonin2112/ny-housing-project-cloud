# NY Housing Project

A high-performance REST API for analyzing New York housing market data, built with **FastAPI**, **PostgreSQL**, **Redis**, and **Nginx** — horizontally scaled across 3 app instances with built-in load testing.

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │            Nginx (port 5000)         │
                        │        Round-robin load balancer     │
                        └──────────┬────────────┬─────────────┘
                                   │            │
                    ┌──────────────┼────────────┼──────────────┐
                    ▼             ▼            ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │  web_1   │  │  web_2   │  │  web_3   │
              │ FastAPI  │  │ FastAPI  │  │ FastAPI  │
              │ 4 workers│  │ 4 workers│  │ 4 workers│
              └────┬─────┘  └────┬─────┘  └────┬─────┘
                   │             │              │
           ┌───────▼─────────────▼──────────────▼──────┐
           │                                            │
    ┌──────▼──────┐                           ┌────────▼───────┐
    │ PostgreSQL  │                           │     Redis      │
    │  (housing   │                           │  (60s TTL cache│
    │   dataset)  │                           │   per query)   │
    └─────────────┘                           └────────────────┘
```

**Stack:**
- **Nginx** — reverse proxy + keep-alive connection pooling (64 persistent conn/upstream)
- **FastAPI + uvloop + httptools** — async API, 3 instances × 4 workers = 12 processes
- **asyncpg** — async PostgreSQL driver with connection pooling (10–10 connections)
- **Redis** — query result caching (60-second TTL)
- **PostgreSQL** — tuned for throughput (256MB shared buffers, async commit off, 300 max connections)

## Dataset

~500k+ NY property records loaded from `housing.csv` (~1.3 GB) with 18 columns: price, beds, baths, square footage, locality, geolocation, etc.

A composite index on `(LOCALITY, PRICE DESC)` optimizes the most common query patterns.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check — returns total row count |
| `GET` | `/stats` | Aggregated statistics per locality (cached) |
| `GET` | `/houses` | Property listings with filters (cached) |

### `/houses` query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `locality` | string | Filter by NY locality name |
| `limit` | int | Max number of results to return |

## Getting Started

### Prerequisites

- Docker & Docker Compose

### Run

```bash
git clone <repo-url>
cd ny-housing-project
docker compose up --build -d
```

The API is available at **http://localhost:5000**

> The first startup may take a few minutes — PostgreSQL loads the full housing dataset on init.

### Endpoints to try

```bash
# Health check
curl http://localhost:5000/

# Housing stats by locality
curl http://localhost:5000/stats

# Filter houses in Manhattan, top 20
curl "http://localhost:5000/houses?locality=Manhattan&limit=20"
```

## Benchmark

A built-in benchmark server with a web UI is available at **http://localhost:8080** after startup.

It runs [K6](https://k6.io/) load tests against the Nginx cluster and streams results in real-time via SSE.

**Default test config:** 100 virtual users × 100,000 iterations against `/houses` with randomized locality queries.

### Run benchmarks manually

```bash
# Python benchmark
python3 benchmark.py

# K6 script directly
k6 run benchmark_k6.js

# Override target URL
BASE_URL=http://myserver:5000 k6 run benchmark_k6.js
```

## Configuration

Environment variables are set in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `ny_housing` | Database name |
| `POSTGRES_USER` | `user` | DB user |
| `POSTGRES_PASSWORD` | `mdpdev` | DB password |

## Project Structure

```
ny-housing-project/
├── app/
│   └── app.py              # FastAPI application
├── benchmark/
│   └── server.py           # Benchmark web UI server
├── db/
│   └── init.sql            # DB schema + data loading
├── nginx.conf              # Load balancer config
├── docker-compose.yaml     # Full infrastructure
├── benchmark_k6.js         # K6 load test script
├── benchmark.py            # Python benchmark script
└── housing.csv             # NY housing dataset (~1.3 GB)
```
