# Export Agent — AI-Assisted Export Compliance Engine

[![CI](https://github.com/AdityaShekhawat0504/export-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/AdityaShekhawat0504/export-agent/actions/workflows/ci.yml)

**A FastAPI service that classifies export shipments into HS codes with an LLM, screens the destination and the counterparty, remembers human corrections, and returns an approve / review / block decision with a stored reason.**

The core pattern is general: *a case comes in → AI classifies it → explicit rules decide → only the uncertain cases go to a human → human corrections are remembered.* The same structure fits order intake, returns triage or support-inbox routing in operations teams.

## Problem

Every export shipment needs an HS (Harmonized System) tariff code and a sanctions
check before it can ship. Doing this by hand is slow and inconsistent, and pure-LLM
classification is not trustworthy enough to act on alone. Export Agent combines an
LLM classifier, a memory of human-verified answers, and explicit risk rules, and
routes uncertain cases to a human instead of guessing.

## How it works

```mermaid
flowchart LR
    A[POST /shipments] --> B{Memory hit?<br/>conf ≥ 0.95 or<br/>human feedback}
    B -- yes --> D[HS code from memory]
    B -- no --> C[OpenAI gpt-4o-mini<br/>classifier]
    C --> E[(Save to memory)]
    C --> D2[HS code from AI]
    D --> R{Risk engine}
    D2 --> R
    R -- "destination in IR, KP, SY, CU" --> X[blocked]
    R -- "counterparty on denied-parties list" --> X
    R -- "near match, no HS code,<br/>or confidence < 0.75" --> V[review]
    R -- otherwise --> OK[approved]
    F[POST /feedback] -->|"correct HS code,<br/>confidence 1.0"| E
```

1. A shipment arrives with a product description, destination country and counterparty.
2. The description is fingerprinted and looked up in memory. Human-verified (or ≥ 0.95
   confidence) entries are reused without calling the LLM.
3. Otherwise the LLM returns an HS code (`XXXX.XX`), which is stored in memory.
4. The risk engine blocks sanctioned destinations and counterparties that match the
   denied-parties list (fuzzy match on normalised names), sends near matches,
   unclassified and low-confidence results to review, and approves the rest. The
   decision is stored with its reason and source.
5. `POST /feedback` lets a human correct a code; future shipments of that product use it.

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Results

There is no accuracy benchmark or labelled evaluation set in this repository, so no
classification-accuracy numbers are claimed. What the code does guarantee, and the
test suite (`backend/tests/`, 47 tests, ~1 s) checks:

| Rule | Value in code |
|---|---|
| Sanctioned destinations (always blocked) | `IR`, `KP`, `SY`, `CU` |
| Denied-party match on counterparty | score `≥ 0.90` → blocked, `≥ 0.75` → review |
| Manual-review threshold | confidence `< 0.75` |
| Memory reuse threshold | confidence `≥ 0.95`, or any human feedback |
| Confidence assigned to an LLM answer | `0.9` (fixed) |
| Confidence of human feedback | `1.0` |
| No API key, API error or unparseable answer | `UNKNOWN` at `0.0` → always review, never stored in memory |

## Quickstart

Requires Python 3.12+ and Docker (for Postgres). No OpenAI key needed to run.

```bash
git clone https://github.com/AdityaShekhawat0504/export-agent.git
```

```bash
cd export-agent && docker compose up -d db
```

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
cp .env.example .env && set -a && source .env && set +a
```

```bash
uvicorn app.main:app --reload
```

Then, in another terminal:

```bash
curl -s -X POST localhost:8000/shipments -H 'Content-Type: application/json' \
  -d '{"description":"Electric motor","destination_country":"DE","counterparty_name":"ACME GmbH"}'
```

Interactive API docs: <http://localhost:8000/docs>. Set `OPENAI_API_KEY` in `.env`
to use the real classifier. Without it nothing is guessed: shipments come back as
`review` ("No HS classification available") until a human supplies a code.

### Demo without an API key

```bash
# 1. Unknown product: goes to a human
curl -s -X POST localhost:8000/shipments -H 'Content-Type: application/json' \
  -d '{"description":"Office chair","destination_country":"DE","counterparty_name":"ACME GmbH"}'
# → "status": "review", "decision_reason": "No HS classification available (ai)"

# 2. A human supplies the code once
curl -s -X POST localhost:8000/feedback -H 'Content-Type: application/json' \
  -d '{"description":"Office chair","hs_code":"9401.31"}'

# 3. Same product again: reused from memory and approved
curl -s -X POST localhost:8000/shipments -H 'Content-Type: application/json' \
  -d '{"description":"office chair","destination_country":"DE","counterparty_name":"ACME GmbH"}'
# → "status": "approved", "source": "memory"

# 4. Same product to a listed party: blocked, with the reason
curl -s -X POST localhost:8000/shipments -H 'Content-Type: application/json' \
  -d '{"description":"office chair","destination_country":"DE","counterparty_name":"Rosoboronexport JSC"}'
# → "status": "blocked", "decision_reason": "Denied party match: Rosoboronexport (score 1.0) (memory)"
```

### Run the tests

```bash
cd backend && pip install -r requirements-dev.txt && ruff check . && pytest -q
```

Tests need no database, network, or API key (OpenAI is mocked; SQLite in memory).

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/health` | – | `{"status": "ok"}` |
| `POST` | `/shipments` | `description`, `destination_country`, `counterparty_name` | Shipment with `hs_code`, `confidence`, `source`, `status`, `blocked`, `decision_reason` |
| `GET` | `/shipments` | – | All shipments |
| `POST` | `/feedback` | `description`, `hs_code` | Updated memory entry |

## Stack

Python · FastAPI · SQLAlchemy 2 (async) · asyncpg · PostgreSQL 15 · OpenAI API
(`gpt-4o-mini`) · pytest · Ruff · GitHub Actions

## Limitations

- **Confidence is not measured.** LLM answers always get 0.9; it is not derived from
  the model, so the review threshold does not reflect real uncertainty.
- **AI answers are stored but not reused**, because 0.9 is below the 0.95 memory
  threshold. Only human feedback short-circuits the LLM.
- **Exact-match memory.** Fingerprints ignore case and surrounding whitespace only;
  near-duplicate descriptions miss.
- **Sample sanctions data.** Four hard-coded country codes and a small sample of
  publicly listed entities. Real use needs the full EU consolidated and OFAC SDN lists
  (`DENIED_PARTIES_FILE`), aliases, and a review of the 0.90 / 0.75 match thresholds;
  partial names (e.g. "Iran Shipping Lines") can miss.
- **Prototype infrastructure.** No auth, no migrations (tables via `create_all`),
  no pagination on `GET /shipments`.

## Author

Aditya Singh Shekhawat
