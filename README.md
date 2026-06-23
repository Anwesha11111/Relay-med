# Relay-med (SecureMed AI Health Companion)

> Trust-aware, full-stack AI health application with causal inference, differential privacy, and hospital-grade security.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- pip

### 2. Install dependencies
```bash
cd Relay-med
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env
# Edit .env — set GEMINI_API_KEY and/or OLLAMA_BASE_URL,
# and (optionally) GOOGLE_CLIENT_ID to enable Google sign-in.
```

### 4. Run the backend
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run the frontend (separate terminal)
```bash
cd "relay-med-frontend (1)"
npm install
npm run dev          # Vite dev server; talks to the backend at http://localhost:8000
```
The frontend reads `VITE_API_URL` (defaults to `http://localhost:8000`).

### 6. Seed synthetic data (optional)
```bash
python data_gen/generate.py --days 30
```

---

## Architecture Overview

```
Data Trust & Ingestion  →  Prediction & Causality  →  Explainability  →  Conversational UI
```

| Layer | Key Services |
|---|---|
| Ingestion | `IngestionService`, `TrustScorer`, `ConsentManager` |
| Prediction | `HealthGraph`, `RuleEngine`, `TGNNEngine`*, `CausalEngine`* |
| Explainability | `ExplainabilityService`, `DifferentialPrivacyEngine` |
| Conversation | `ConversationService`, `LLMAdapter` (Ollama \| Gemini) |
| Security | `EncryptionService` (AES-256-GCM), `AuditLogger`, `EmergencyTriageService` |

*Phase 2/3 stubs — activate by installing PyTorch Geometric / DoWhy.

---

## LLM Switching

Set `LLM_PROVIDER` in `.env`:

| Value | Backend |
|---|---|
| `gemini` | Google Gemini API (requires `GEMINI_API_KEY`) |
| `ollama` | Local Ollama (requires `OLLAMA_BASE_URL`) |

---

## Authentication

Real accounts with app-issued session tokens (HS256 JWT). No third-party auth
library required — signing and password hashing use the Python standard library.

- **Email/password** — works out of the box. Passwords are PBKDF2-HMAC-SHA256
  hashed; users persist to `data/auth/users.json`.
- **Google** — set `GOOGLE_CLIENT_ID` in `.env`. The frontend renders the
  official Google Identity Services button; the backend verifies the returned
  ID token server-side before issuing a session token.
- **X (Twitter)** — placeholder in the UI (requires paid API credentials).

To enable Google sign-in:
1. Create an **OAuth Web Client** at
   <https://console.cloud.google.com/apis/credentials>.
2. Add your frontend origin (e.g. `http://localhost:3000`) under
   *Authorized JavaScript origins*.
3. Put the client ID in `.env` as `GOOGLE_CLIENT_ID=...` and restart the backend.

Protected routes use `Authorization: Bearer <token>`. Set `AUTH_MODE=jwt` to
require it on the user-scoped endpoints (default `header` keeps dev open).

---

## API Reference

Interactive docs available at **http://localhost:8000/api/docs** (Swagger UI).

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create an email/password account → `{token, user}` |
| POST | `/api/v1/auth/login` | Email/password login → `{token, user}` |
| POST | `/api/v1/auth/google` | Verify a Google credential → `{token, user}` |
| GET  | `/api/v1/auth/me` | Current user (requires `Authorization: Bearer`) |
| POST | `/api/v1/ingest` | Submit a vital record |
| POST | `/api/v1/consent` | Grant/revoke consent |
| GET  | `/api/v1/consent/{user_id}` | List consent records |
| GET  | `/api/v1/reports/latest` | Generate explainability reports |
| GET  | `/api/v1/reports/vitals/{type}` | Vital history |
| POST | `/api/v1/conversation/chat` | Chat with AI (SSE streaming) |
| GET  | `/api/v1/conversation/summary` | AI health summary |
| GET  | `/api/v1/audit/logs` | Query audit log |
| GET  | `/health` | System health check |

---

## Running Tests

```bash
# Unit tests
pytest backend/tests/unit/ -v

# Integration tests
pytest backend/tests/integration/ -v

# All tests
pytest backend/tests/ -v
```

---

## Phased Delivery

| Phase | Status | Features |
|---|---|---|
| Phase 1 MVP | ✅ Active | Rule engine, trust scoring, encryption, audit, chat |
| Phase 2 T-GNN | 🔧 Stub | Temporal Graph Neural Network risk prediction |
| Phase 3 Causal AI | 🔧 Stub | DoWhy causal inference + counterfactuals |

---

## Security

- **Encryption**: AES-256-GCM via Python `cryptography` library
- **Key derivation**: PBKDF2-HMAC-SHA256 from `SECUREMED_MASTER_KEY`
- **Differential privacy**: Laplace mechanism on exported statistics
- **Anti-Hacking Noise Protocol**: Calibrated medical-grade noise injection at ingestion to protect raw data from AI model reconstruction
- **Audit log**: Append-only JSONL, auto-archives at 1 GB
- **Consent**: Per-stream, per-user, version-tracked
- **Emergency triage**: Red flags fire regardless of trust score

---

## Folder Structure

```
Relay-med/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Central config
│   ├── api/v1/routes/       # auth, ingest, consent, reports, conversation, audit, feedback, bias
│   ├── api/v1/dependencies.py  # auth / consent / rate-limit / RBAC guards
│   ├── services/            # All business logic services (incl. auth_service)
│   ├── models/              # Dataclasses
│   ├── rules/               # clinical_rules.yaml
│   └── tests/               # unit + integration + property tests
├── relay-med-frontend (1)/  # React 19 + TanStack Start (SSR), deploys to Cloudflare
│   └── src/
│       ├── routes/          # file-based routes (dashboard, my-health, reports, …)
│       ├── components/      # LoginPage, RelayGuidePanel (chat), Sidebar, …
│       ├── hooks/           # useAuth (real backend auth), useNotifications
│       └── lib/api.ts       # API base + bearer-token fetch helper
├── data_gen/
│   ├── generate.py          # Synthetic data generator
│   └── validate.py          # KL divergence validator
├── requirements.txt
├── render.yaml              # Backend deploy (Render)
└── .env.example
```
