# AI Sales Agent

> Autonomous B2B sales agent powered by Claude. Finds leads, scores them against your ICP, writes personalized cold emails, qualifies inbound leads via conversation, and handles follow-ups — all without human intervention until a deal is ready to close.

**Stack:** Python 3.12 · FastAPI · LangGraph · Claude (Anthropic) · PostgreSQL · Redis · SendGrid · n8n

---

## How it works

There are two independent pipelines that run in parallel:

### Outbound — goes and finds customers

```
Apollo / Hunter / LinkedIn / CSV
           │
           ▼
    ┌─────────────┐
    │  Lead Finder │  Deduplicates by email across all sources
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │    Scorer    │  Claude reads each lead profile and scores 1–100
    │              │  against your ICP (config/icp.yaml)
    │              │  Drops anything below threshold (default: 60)
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ Personalizer │  Claude writes a hyper-personalized cold email
    │              │  per lead — references their role, company, pain
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   Outreach   │  ← HUMAN APPROVAL CHECKPOINT
    │              │  You review draft → approve → SendGrid sends
    └─────────────┘
```

### Inbound — qualifies people who reach out to you

A visitor contacts you via chat, form, or email. The agent runs a BANT qualification conversation — one question at a time, adapting to answers — until it has enough signal to score the lead.

```
Lead writes "Hi, interested in your product"
           │
           ▼
    Agent: "What's the core problem you're trying to solve?"
           │
    Lead answers...
           │
    Agent: "What budget range are you working with?"
           │
    Lead answers...
           │
    ... (collects Budget, Authority, Need, Timeline)
           │
           ▼
    Score ≥ 70  →  "Great! Book 20 min: calendly.com/you/demo?email=..."
    Score 40–69 →  Nurture sequence
    Score < 40  →  Politely disqualified
```

**Example — real conversation output:**

```json
{
  "qualified": true,
  "score": 100,
  "bant": {
    "budget": "25K/yr",
    "authority": "CEO",
    "need": "automate outbound sales prospecting",
    "timeline": "6 weeks"
  },
  "next_message": "Great! Book 20 min here: https://calendly.com/you/demo?email=ceo@acme.io"
}
```

### Follow-up — handles replies automatically

```
Lead replies to cold email
           │
           ▼
    Classifier: interested / objection / not interested
           │
    ┌──────┴───────┐
    │              │
 Objection      Interested
    │              │
 Handle it     Book call via Calendly
 (Claude writes  + sync to HubSpot
  a response)
```

---

## Architecture

```
n8n (triggers & orchestration)
    │
    │  HTTP
    ▼
FastAPI (api/main.py)
    │
    │  LangGraph StateGraph
    ▼
┌─────────────────────────────────────┐
│  Agent Pipeline                     │
│  lead_finder → scorer → personalizer│
│  → [CHECKPOINT] → outreach          │
└─────────────────────────────────────┘
    │
    ├── Claude API (all intelligence)
    ├── PostgreSQL (leads, conversations)
    ├── Redis (state, dedup cache)
    └── SendGrid / Calendly / HubSpot
```

All Claude prompts are plain markdown files in `prompts/` — edit them to change agent behavior without touching code.

---

## Quick start

### Prerequisites
- Python 3.12+
- Docker or Podman
- Anthropic API key
- Apollo API key (for outbound lead search)

### 1. Clone and install

```bash
git clone https://github.com/sbot666/ai-sales-agent
cd ai-sales-agent
pip install -e ".[dev]"
```

### 2. Start Postgres + Redis

```bash
docker compose up -d postgres redis
# or with podman:
podman compose up -d postgres redis
```

### 3. Run migration

```bash
psql $DATABASE_URL -f db/migrations/001_initial.sql
```

### 4. Configure `.env`

```bash
cp .env.example .env
```

| Variable | Required for | Where to get |
|----------|-------------|--------------|
| `ANTHROPIC_API_KEY` | everything | [console.anthropic.com](https://console.anthropic.com) |
| `ANTHROPIC_BASE_URL` | proxy users | your proxy base URL |
| `APOLLO_API_KEY` | outbound | [apollo.io](https://apollo.io) → Settings → API |
| `SENDGRID_API_KEY` | outbound | [sendgrid.com](https://sendgrid.com) |
| `SENDGRID_FROM_EMAIL` | outbound | verified sender in SendGrid |
| `CALENDLY_EVENT_URL` | inbound | your Calendly event link |
| `HUBSPOT_ACCESS_TOKEN` | CRM sync | HubSpot private app token |
| `SLACK_BOT_TOKEN` | alerts | Slack bot token |
| `SCORE_MIN` | scoring | minimum score to pass (default: `60`) |

### 5. Define your ICP

Edit `config/icp.yaml` — this is how the scorer knows who's a good lead:

```yaml
industries:
  - SaaS
  - B2B Software
titles:
  - CEO
  - VP Sales
  - Head of Growth
company_size:
  min: 10
  max: 500
keywords:
  - sales automation
  - outbound
  - lead generation
```

### 6. Start the API

```bash
uvicorn api.main:app --port 8000 --reload
```

Health check: `curl http://localhost:8000/health`

---

## API reference

### Outbound — run a campaign

```bash
curl -X POST http://localhost:8000/api/run/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "apollo_query": {
      "job_titles": ["CEO", "VP Sales"],
      "industries": ["SaaS"],
      "employee_ranges": ["11,50", "51,200"]
    }
  }'
```

### Inbound — qualify a lead (stateless, call on each message)

```bash
curl -X POST http://localhost:8000/api/run/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "email": "lead@company.com",
    "messages": [
      {"role": "user", "content": "Hi, interested in your product"},
      {"role": "assistant", "content": "What core problem are you trying to solve?"},
      {"role": "user", "content": "We need to automate our SDR team"}
    ]
  }'
```

Pass the full conversation history each time. The agent remembers nothing — you own the state.

### Approve outreach draft

```bash
curl -X POST http://localhost:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 42, "approved": true}'
```

### Handle email reply

```bash
curl -X POST http://localhost:8000/api/reply \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 42, "reply_text": "Sounds interesting, tell me more"}'
```

---

## n8n automation

Import workflows from `n8n/workflows/` into your n8n instance to automate triggers:

| Workflow | Trigger | Does |
|----------|---------|------|
| `outbound-run.json` | Cron / manual | Runs full outbound pipeline |
| `inbound-intake.json` | Webhook | Routes inbound messages to qualifier |
| `csv-upload.json` | File drop | Imports leads from CSV |
| `reply-tracker.json` | Email webhook | Sends replies to follow-up agent |
| `crm-sync.json` | Lead qualified | Syncs hot leads to HubSpot |
| `slack-alert.json` | Lead qualified | Posts to `#sales-alerts` Slack channel |

---

## Customizing behavior

Everything Claude does is controlled by markdown prompts — no code changes needed:

| File | Controls |
|------|---------|
| `prompts/scorer.md` | How leads are scored, what signals matter |
| `prompts/personalizer.md` | Email tone, structure, personalization depth |
| `prompts/inbound_qualifier.md` | BANT question flow, scoring rules |
| `prompts/follow_up.md` | Objection handling, reply classification |
| `config/sequences/` | Email sequence configs per goal (demo, trial, reply) |

---

## Project structure

```
agents/          LangGraph nodes — one file per agent
api/             FastAPI app and all endpoints
config/          ICP, thresholds, email sequences
db/              SQLAlchemy models + Postgres migration
n8n/workflows/   Ready-to-import n8n JSONs
prompts/         Claude system prompts (plain markdown)
tools/           API clients: Apollo, Hunter, SendGrid, Calendly, HubSpot
tests/           Full test suite
```

---

## License

MIT
