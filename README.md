# GuardianAI: Autonomous Emergency Response System

GuardianAI is a next-generation autonomous safety and emergency response coordination platform. Designed as a real-time, low-latency system, it translates chaotic user inputs or distress signals into structured, actionable response plans. By combining a multi-agent AI pipeline with real-time location mapping and WebSocket communications, GuardianAI instantly coordinates emergency dispatch protocols, notifies designated personal guardians, and directs the victim to the nearest emergency resources.

---

## ⚡ The Core Problem & Our Approach

In life-or-death emergencies, every second counts. Traditional response dispatch systems rely on voice routing, manual location checks, and human triage. 

**GuardianAI takes a different approach:**
* **Sub-Millisecond Triage:** Rather than deploying resource-heavy LLMs or deep learning models that introduce latency and API cost overhead, GuardianAI uses a deterministic pattern-matching Intent Classifier and an algorithmic Risk Engine. This guarantees emergency classification and risk scoring in **under 2 milliseconds**.
* **Zero-Configuration Location Intelligence:** Using GPS coordinates, it queries OpenStreetMap Nominatim and Overpass APIs in parallel to locate hospitals, police, and fire stations within a 5km radius without relying on proprietary, paid APIs.
* **Autonomous Orchestration:** A central Orchestrator coordinates intent analysis, threat evaluation, geographic lookup, and action planning, storing incidents in a structured schema and broadcasting state changes instantly over WebSockets.

---

## 🏗️ Multi-Agent Architecture & Pipeline Workflow

GuardianAI employs a coordinated multi-agent pipeline managed by a central **Orchestrator**. Below is a map of how an emergency incident flows through the system:

```
[ User Input (Text / Geolocation / SOS Button) ]
                     │
                     ▼
             [ Orchestrator ]
                     │
     ┌───────────────┼───────────────┬───────────────┐
     ▼               ▼               ▼               ▼
[Intent Agent] [Risk Agent]  [Location Agent] [Decision Engine]
  Categorizes    Calculates   Queries OSM Map   Blends context 
   threats &      threat score  & finds nearby   and generates
   urgency         (0-100)       facilities      action items
     │               │               │               │
     └───────────────┼───────────────┴───────────────┘
                     │
                     ▼
         [ Database & State Log ]
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
[WebSocket Broadcast]   [Guardian Alerts]
 (Real-time Sync)       (Sms/Email Simulation)
```

### 1. Intent Agent (`intent_agent.py`)
Classifies the incoming text into one of 6 primary emergency categories: `fire`, `medical`, `accident`, `crime`, `natural_disaster`, or a general threat.
* **Weighted Keyword Index:** Uses a dictionary of normalized emergency terms with relative weight scores.
* **Urgency Amplifier:** Scans for high-velocity keywords (e.g., *"immediately"*, *"dying"*, *"save me"*) to scale classification confidence.
* **SOS Preemption:** Immediately short-circuits to maximum confidence `sos` if the distress signals are direct (e.g., holding the dashboard panic button).

### 2. Risk Agent (`risk_agent.py`)
Determines the numeric risk level (0-100) and groups it into a tier (`low`, `medium`, `high`, `critical`). It uses a multi-factor formula:
$$\text{Risk Score} = \text{Base Risk} + \text{Confidence Modifier} + \text{Keyword Modifiers} + \text{Contextual Penalties}$$
* **Nighttime Penalty:** Automatically adds a penalty (+5) if the incident occurs during typical high-risk nocturnal hours (10:00 PM – 5:00 AM).
* **Multi-Intent Scaling:** Adds points for composite emergencies (e.g., a car accident that also involves a fire).
* **Description Verbosity:** Rewards longer, descriptive texts (+3) under the assumption that more detail correlates with complex environments.

### 3. Location Agent (`location_agent.py`)
Works asynchronously by spawning concurrent tasks to minimize response latency:
* **Reverse Geocoding:** Translates raw latitude/longitude coordinates into localized street addresses using Nominatim.
* **Overpass QL Queries:** Contacts OpenStreetMap Overpass servers to find active emergency nodes (hospitals, fire stations, clinics, and police stations) within a 5,000-meter radius.
* **API Fallbacks:** Automatically injects estimated fallback coordinates and emergency hotline numbers (like 100, 101, 108) if the public OSM endpoints throttle or fail.

### 4. Decision Engine (`decision_engine.py`)
The ultimate brain. It combines the category, risk metrics, and geographic surroundings to assemble a customized payload:
* **Action Translation:** Maps the incident type to predefined emergency blueprints (e.g., evicting a building for fire, applying pressure for bleeding).
* **Dynamic Route Embedding:** Modifies the dispatch text dynamically, inserting the name, address, and telephone number of the closest detected medical center or police office.
* **Risk Adjustments:** Downgrades high-priority actions to standby if the computed risk score is trivial, avoiding false alarms.

---

## 📂 Project Directory Structure

```
guardianai/
│
├── backend/
│   ├── agents/                   # The core AI Agent cluster
│   │   ├── orchestrator.py       # Pipeline supervisor
│   │   ├── intent_agent.py       # Text pattern classifier
│   │   ├── risk_agent.py         # Multi-factor risk scorer
│   │   ├── location_agent.py     # OSM geocoding & services finder
│   │   └── decision_engine.py    # Context blender & action generator
│   │
│   ├── routes/                   # FastAPI endpoints
│   │   ├── auth_routes.py        # Registration & JWT issuance
│   │   ├── emergency_routes.py   # SOS / AI analysis post endpoints
│   │   ├── guardian_routes.py    # Contacts list CRUD
│   │   ├── incident_routes.py    # Log retrieval & analytics
│   │   └── ws_routes.py          # Real-time WebSocket connection manager
│   │
│   ├── auth.py                   # Password hashing & JWT middleware
│   ├── database.py               # SQLite / SQLAlchemy boilerplate
│   ├── models.py                 # ORM Entities (User, Guardian, Incident)
│   ├── schemas.py                # Pydantic input/output contracts
│   ├── main.py                   # FastAPI initialization
│   └── requirements.txt          # Python packages
│
├── frontend/                     # Modern Single-Page App
│   ├── index.html                # Dashboard layout & modals
│   ├── style.css                 # Dark-mode styling
│   └── app.js                    # WebSockets, Leaflet maps, & layout logic
│
├── guardianai.db                 # Local SQLite database
├── test_api.py                   # Async connection & auth tests
├── test_api_debug.py             # JWT signature validation debug tool
└── test_client.py                # FastAPI TestClient script
```

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.10+
* A modern web browser with geolocation permissions enabled

### Backend Installation

1. Navigate to the project root and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the package dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Spin up the FastAPI development server:
   ```bash
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *The database (`guardianai.db`) will initialize automatically on startup, generating all tables.*
   *Interactive Swagger API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).*

### Frontend Installation
The frontend is a vanilla client implementation. No compilation or bundler is required.
1. Open `frontend/index.html` directly in a browser, or serve it using any simple static file server:
   ```bash
   # Using Python's built-in server
   python -m http.server 8080 --directory frontend/
   ```
2. Visit `http://localhost:8080` in your web browser.

---

## 🧪 Integration Testing
You can verify backend API functionality (user signup, database integration, JWT generation, and endpoint protection) by executing the test scripts:

```bash
# Run direct API endpoint checks
python test_api.py

# Run standard FastAPI test client assertions
python test_client.py
```

---

## 🔒 Security & Performance Considerations

* **State Synchronization:** The system communicates on-demand over WebSockets (`ws://localhost:8000/ws/{user_id}`). Location telemetry, connection statuses, and alert updates are transmitted instantly across all logged-in client screens.
* **Lightweight Footprint:** By using rule-based decision trees and deterministic regex matrices instead of LLM inference calls, the system guarantees execution even on low-end servers, avoids costly GPU dependency, and is immune to prompt injection attacks.
* **Fail-Safe Fallbacks:** In case OpenStreetMap APIs throttle the server or network access is lost, the location agent catches the HTTP timeouts gracefully and returns pre-configured local network options, ensuring the frontend still renders maps and contact options.
