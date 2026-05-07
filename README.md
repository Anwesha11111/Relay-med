# Relay-med (SecureMed AI Health Companion)

> Trust-aware, full-stack AI health application with causal inference, differential privacy, and hospital-grade security.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- pip

### 2. Install dependencies
```bash
cd secure-med-ai-companion
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env
# Edit .env — set GEMINI_API_KEY and/or OLLAMA_BASE_URL
```

### 4. Run the backend
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 9000
```

### 5. Open the UI
Navigate to **http://localhost:9000** in your browser.

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

## API Reference

Interactive docs available at **http://localhost:9000/api/docs** (Swagger UI).

| Method | Endpoint | Description |
|---|---|---|
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
secure-med-ai-companion/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Central config
│   ├── api/v1/routes/       # ingest, consent, reports, conversation, audit
│   ├── services/            # All business logic services
│   ├── models/              # Dataclasses
│   ├── rules/               # clinical_rules.yaml
│   └── tests/               # unit + integration tests
├── frontend/
│   ├── index.html           # Single-page application
│   ├── css/                 # base, dashboard, chat, consent
│   └── js/                  # api, charts, dashboard, chat, consent
├── data_gen/
│   ├── generate.py          # Synthetic data generator
│   └── validate.py          # KL divergence validator
├── requirements.txt
└── .env.example
```
