# Relay-med — AI Health Companion

## Project Summary

**Relay-med** is a trust-aware, AI-powered predictive healthcare companion that provides personalized health insights, medicine suggestions (with safety disclaimers), and preventive wellness guidance. It combines real-time health data analysis with explainable AI to deliver actionable, patient-friendly health recommendations.

---

## Key Features

### 1. AI-Powered Health Chat (Relay Guide)
- Interactive conversational AI that answers health questions
- Suggests medicines with mandatory "consult your doctor" disclaimers
- Covers 20+ medical topics: headaches, burns, bruises, diabetes, allergies, cold/flu, stomach issues, back pain, dental, skin conditions, eye/ear problems, first aid, and more
- Personalized responses based on user's actual health data
- Built-in fallback knowledge base works without any API key
- Optional Google Gemini / Ollama LLM integration for advanced responses
- LangChain integration with PubMed for evidence-based answers
- Prescription note detection — blocks fake prescription generation

### 2. Medical Data Input & Device Sync
- **Glucometer** — Enter blood glucose readings
- **BP Machine** — Systolic/diastolic blood pressure
- **Pulse Oximeter** — SpO2 and heart rate
- **Thermometer** — Body temperature
- **Fitbit / Wearable** — Steps and sleep data
- **Medical History** — Known conditions and current medications
- **Report Upload** — Upload PDFs, images of blood tests, prescriptions, X-rays

### 3. Personalized Health Insights
- AI responses adapt based on user's entered medical data
- Visible personalization status indicator in chat
- Toggle data sharing on/off in Settings — immediately affects responses
- When data sharing is OFF, user sees generic guidance with clear indicator
- When ON, AI references actual readings (BP, glucose, SpO2, etc.)

### 4. Nearby Healthcare Services
- **Find Doctors Near Me** — Opens Google Maps with nearby clinics
- **Find Pharmacies Near Me** — Locate nearby pharmacies
- **Emergency Call (112/911)** — One-tap emergency dial

### 5. Health Dashboard
- Real-time vital signs display (Heart Rate, Sleep, Steps, Hydration, Calories, Stress)
- Trend charts with 14-day visualization
- Color-coded health status indicators

### 6. Health Alerts & Notifications
- Prioritized notifications based on severity (High/Medium/Low)
- Anomaly detection alerts (elevated stress, dehydration, etc.)
- Weekly wellness report notifications
- Medicine interaction warnings
- Mark as read / dismiss functionality

### 7. Multi-User Authentication
- Google OAuth login (simulated)
- Twitter OAuth login (simulated)
- Email/password login
- Session persistence via localStorage
- User profile with avatar and provider info

### 8. Device Synchronization
- Cross-device sync (Desktop, Mobile, Tablet)
- Same account = same data across devices
- Real-time sync status display

### 9. Privacy & Data Control
- **Master data sharing toggle** — completely disable AI access to health data
- Granular controls: vital signs, activity data, medical history, documents
- Data permissions audit log
- AES-256 encryption for all health data
- Differential privacy techniques
- HIPAA-aware consent management

### 10. What-If Health Simulator
- Simulate health scenarios ("What if I walk 30 min daily?")
- Causal pathway visualization
- 6-month health forecast

### 11. Trust & Explainability Center
- Trust scoring for data reliability
- Explainability reports for AI decisions
- Bias auditing
- Audit trail logging

### 12. Wellness Reports & Health Library
- Generated wellness reports
- Health education resources
- Evidence-based health articles

---

## Objectives

1. **Personalized Health Intelligence** — Provide tailored health guidance based on individual user data from medical devices and wearables
2. **Trust-Aware AI** — Ensure AI transparency through explainability, trust scoring, and bias auditing
3. **Safety-First Medicine Suggestions** — AI can suggest medicines but always with mandatory doctor-consultation disclaimers; blocks fake prescription notes
4. **Privacy by Design** — Full user control over data sharing, AES-256 encryption, differential privacy, consent management
5. **Accessibility** — Work without API keys (built-in fallback), answer common medical questions, provide emergency contacts and nearby services
6. **Preventive Wellness** — Trend detection, anomaly alerts, health forecasting, and lifestyle recommendations

---

## Tools & Technologies

### Backend
| Tool/Library | Purpose |
|---|---|
| **Python 3.12** | Core backend language |
| **FastAPI** | REST API framework with automatic OpenAPI docs |
| **Uvicorn** | ASGI server for production deployment |
| **Pydantic** | Data validation and settings management |
| **Google Generative AI** | Gemini LLM integration for AI chat |
| **LangChain** | LLM orchestration and PubMed integration |
| **NetworkX** | Health data graph modeling (causal pathways) |
| **Cryptography** | AES-256 encryption for health data |
| **BioPython** | Biomedical data processing |
| **HTTPX** | Async HTTP client for Ollama integration |
| **PyYAML** | Configuration file parsing |
| **Pytest** | Testing framework |

### Frontend
| Tool/Library | Purpose |
|---|---|
| **React 19** | UI framework |
| **TypeScript** | Type-safe development |
| **TanStack Router** | File-based routing with SSR support |
| **TanStack React Query** | Server state management |
| **Vite 7** | Build tool and dev server |
| **Recharts** | Data visualization (health trend charts) |
| **Lucide React** | Icon library |
| **Tailwind CSS 4** | Utility-first styling |
| **Radix UI** | Accessible UI primitives |
| **Sonner** | Toast notifications |

### Deployment
| Platform | Purpose |
|---|---|
| **Render** | Backend (FastAPI) hosting |
| **Vercel** | Frontend (React) hosting |
| **Cloudflare Workers** | Edge deployment (optional) |

---

## Architecture & Methodology

### System Architecture
```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND (React)                   │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌─────────┐ │
│  │Dashboard│ │ My Health│ │Relay Guide│ │Settings │ │
│  │         │ │(Data In) │ │  (Chat)   │ │(Privacy)│ │
│  └─────────┘ └──────────┘ └───────────┘ └─────────┘ │
│           localStorage (health data, auth)            │
└───────────────────────┬──────────────────────────────┘
                        │ REST API (JSON)
┌───────────────────────┴──────────────────────────────┐
│                   BACKEND (FastAPI)                    │
│  ┌────────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │Conversation Svc│  │ LLM Adapter  │  │Rule Engine│ │
│  │(Chat + Safety) │  │(Gemini/Ollama│  │(Anomaly   │ │
│  │                │  │  /Fallback)  │  │ Detection)│ │
│  └────────────────┘  └──────────────┘  └───────────┘ │
│  ┌────────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │Trust Scorer    │  │Explainability│  │Bias Audit │ │
│  │                │  │   Service    │  │           │ │
│  └────────────────┘  └──────────────┘  └───────────┘ │
│  ┌────────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │Consent Manager │  │  Encryption  │  │Audit Log  │ │
│  │                │  │  (AES-256)   │  │           │ │
│  └────────────────┘  └──────────────┘  └───────────┘ │
└──────────────────────────────────────────────────────┘
```

### Data Flow
1. **User enters health data** (My Health page) → saved to localStorage
2. **User asks question in chat** → health data appended to message
3. **Backend receives message** → conversation service builds prompt with health context
4. **LLM Adapter routes to** → Gemini API (if key set) / Ollama (local) / Built-in fallback
5. **Response is processed** → medicine disclaimers added, prescription notes blocked
6. **Response displayed** → with personalization indicator and proper markdown rendering

### Safety Architecture
- **Prescription Note Detection** — Regex-based detection blocks fake Rx: / Sig: / Disp: formatting
- **Medicine Disclaimer Injection** — Automatically appended when responses mention medications
- **Emergency Triage** — SpO2 < 90% and chest pain > 7/10 trigger immediate alerts
- **Trust Scoring** — Data reliability weighted by source, completeness, and recency

---

## How to Run the Project

### Prerequisites
- **Python 3.10+** installed
- **Node.js 18+** and npm installed
- (Optional) A Google Gemini API key for AI-powered responses

### Step 1: Clone the Repository
```bash
git clone https://github.com/Anwesha11111/Relay-med.git
cd Relay-med
```

### Step 2: Set Up the Backend
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```bash
# Copy the example env file
copy .env.example .env
# (or on macOS/Linux: cp .env.example .env)
```

Edit the `.env` file:
```env
# For AI-powered chat (optional — app works without this):
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# OR use local Ollama (if installed):
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434

# If you don't have any API key, the app uses the built-in
# health knowledge base automatically (no config needed).
```

> **To get a Gemini API key**: Visit https://aistudio.google.com/apikey, click "Create API Key", and paste it in the `.env` file.

### Step 4: Start the Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs`
- Health check: `http://localhost:8000/health`

### Step 5: Set Up the Frontend
```bash
cd frontend
npm install
```

### Step 6: Start the Frontend
```bash
npm run dev
```
The app will open at `http://localhost:5173` (or the port shown in terminal).

### Step 7: Use the App
1. **Sign in** using Google, Twitter, or Email on the login page
2. **Enter your medical data** on the "My Health" page (glucometer, BP, SpO2, etc.)
3. **Click "Save Data"** — your data is now used to personalize AI responses
4. **Go to Dashboard** and chat with Relay Guide
5. **Ask health questions** — the AI will reference your data
6. **Toggle data sharing** in Settings to see how responses change

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/conversation/chat` | Send a message to the AI |
| GET | `/api/v1/conversation/health-summary` | Get proactive health summary |
| POST | `/api/v1/ingest` | Ingest health data |
| GET | `/api/v1/reports` | Get explainability reports |
| POST | `/api/v1/consent` | Update consent preferences |
| GET | `/api/v1/audit/log` | View audit trail |
| POST | `/api/v1/feedback` | Submit feedback on AI responses |
| GET | `/api/v1/bias/audit` | Run bias audit report |
| GET | `/health` | System health check |

---

## Testing

```bash
# Run all backend tests
python -m pytest test_all_components.py -v

# Run chat-specific tests
python -m pytest test_chat_api.py -v

# Run prescription safety tests
python -m pytest test_prescription_safety.py -v
```

---

## Deployment

### Backend (Render)
1. Push to GitHub
2. Connect repo to [Render](https://render.com)
3. Set environment variables (GEMINI_API_KEY, etc.)
4. Deploy — uses `Procfile` and `render.yaml`

### Frontend (Vercel)
1. Connect the `relay-med-frontend (1)` directory to [Vercel](https://vercel.com)
2. Set `VITE_API_URL` environment variable to your Render backend URL
3. Deploy

---

## License
MIT License — See [LICENSE](./LICENSE) for details.
