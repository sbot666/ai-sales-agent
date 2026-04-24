# AI Sales Agent

Autonomous B2B sales agent. Finds leads, scores them, writes personalized outreach, qualifies inbound via BANT conversation, handles follow-ups.

**Stack:** Python 3.12 · FastAPI · LangGraph · Claude (Anthropic) · PostgreSQL · Redis · SendGrid · n8n

---

## What it does

### Outbound pipeline
1. **Lead Finder** — pulls leads from Apollo.io, Hunter.io, LinkedIn CSV
2. **Scorer** — Claude scores each lead 1–100 against your ICP; drops anything below threshold (default 60)
3. **Personalizer** — Claude writes a personalized cold email per lead
4. **Outreach** — sends via SendGrid after human approval

### Inbound pipeline
Visitor sends a message → agent runs BANT qualification (Budget / Authority / Need / Timeline) → if score ≥ 70, sends Calendly booking link automatically.

### Follow-up
Classifies reply sentiment → handles objections → books calls.

---

## Quick start

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

Edit `.env`:

| Variable | Required | Where to get |
|----------|----------|--------------|
| `ANTHROPIC_API_KEY` | ✅ | [console.anthropic.com](https://console.anthropic.com) |
| `ANTHROPIC_BASE_URL` | optional | Custom proxy URL |
| `APOLLO_API_KEY` | ✅ outbound | [apollo.io](https://apollo.io) → Settings → API |
| `SENDGRID_API_KEY` | ✅ outbound | [sendgrid.com](https://sendgrid.com) |
| `SENDGRID_FROM_EMAIL` | ✅ outbound | Verified sender in SendGrid |
| `CALENDLY_EVENT_URL` | ✅ inbound | Your Calendly event link |
| `HUBSPOT_ACCESS_TOKEN` | optional | HubSpot private app token |
| `SLACK_BOT_TOKEN` | optional | Slack bot token |

### 5. Configure your ICP

Edit `config/icp.yaml` — define your ideal customer profile (industry, company size, titles, keywords). The scorer uses this to rank leads.

### 6. Start the API

```bash
uvicorn api.main:app --port 8000 --reload
```

Check: `http://localhost:8000/health`

---

## API

### Run outbound campaign
```bash
curl -X POST http://localhost:8000/api/run/outbound \
  -H "Content-Type: application/json" \
  -d '{"apollo_query": {"job_titles": ["CEO", "VP Sales"], "industries": ["SaaS"]}}'
```

### Inbound qualifier (chat)
```bash
curl -X POST http://localhost:8000/api/run/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "email": "lead@company.com",
    "messages": [{"role": "user", "content": "Hi, interested in your product"}]
  }'
```

Response while collecting BANT:
```json
{"qualified": null, "next_message": "What's the core problem you're trying to solve?"}
```

Response when done:
```json
{
  "qualified": true,
  "score": 85,
  "bant": {"budget": "25K/yr", "authority": "CEO", "need": "automate outreach", "timeline": "6 weeks"},
  "next_message": "Great! Book 20 minutes here: https://calendly.com/..."
}
```

### Approve outreach draft
```bash
curl -X POST http://localhost:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "approved": true}'
```

### Handle email reply
```bash
curl -X POST http://localhost:8000/api/reply \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "reply_text": "Sounds interesting, tell me more"}'
```

---

## n8n workflows

Import JSON files from `n8n/workflows/` into your n8n instance:

| File | Trigger | What it does |
|------|---------|--------------|
| `outbound-run.json` | Schedule / manual | Runs outbound pipeline |
| `inbound-intake.json` | Webhook | Receives inbound messages, calls `/api/run/inbound` |
| `csv-upload.json` | File drop | Imports leads from CSV |
| `reply-tracker.json` | Email webhook | Forwards replies to `/api/reply` |
| `crm-sync.json` | Pipeline event | Syncs qualified leads to HubSpot |
| `slack-alert.json` | Pipeline event | Posts hot leads to Slack |

---

## Project structure

```
agents/          LangGraph nodes (scorer, personalizer, outreach, follow_up, inbound_qualifier)
api/             FastAPI app + endpoints
config/          ICP definition, scoring thresholds, email sequences
db/              SQLAlchemy models + migrations
n8n/workflows/   n8n workflow JSONs
prompts/         Claude system prompts (markdown)
tools/           API clients (Apollo, Hunter, SendGrid, Calendly, HubSpot)
```

---

## Customizing prompts

All Claude instructions live in `prompts/` as plain markdown files — edit them directly:

- `prompts/scorer.md` — lead scoring criteria
- `prompts/personalizer.md` — email writing style
- `prompts/inbound_qualifier.md` — BANT conversation flow
- `prompts/follow_up.md` — objection handling

---

## License

MIT
