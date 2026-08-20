# ✈️ Real-World Multi-Agent AI Travel Planner

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-UI%20Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Rate--Limit%20Resilient-yellow?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-Multi--Server-green?style=flat-square)
![Database](https://img.shields.io/badge/Postgres-Checkpointer-blue?style=flat-square&logo=postgresql&logoColor=white)

A state-of-the-art, production-grade **autonomous multi-agent travel planning system** built on **LangGraph**. It orchestrates a collaborative swarm of specialized AI agents to construct highly tailored, cost-optimized, and weather-aware travel itineraries. Powered by **Groq** (with automatic model fallback configurations) and presented through a custom **glassmorphic dark-theme Streamlit dashboard**, this application combines real-time data tools with human-in-the-loop review cycles to deliver clean, download-ready travel proposals.

---

## 🗺️ Architectural Workflow

The system is coordinated via a compiled LangGraph **StateGraph** containing custom conditional transitions, parallel agent invocations, and interactive execution checkpoints. Session states are persisted using a PostgreSQL checkpointer (`PostgresSaver`) for live user sessions, failing over gracefully to an in-memory checkpointer (`MemorySaver`) if no database is configured.

```mermaid
flowchart TD
    %% Define Styles %%
    classDef startEnd fill:#0b0f19,stroke:#00f2fe,stroke-width:2px,color:#ffffff;
    classDef guardNode fill:#1e293b,stroke:#f2994a,stroke-width:2px,color:#ffffff;
    classDef superNode fill:#111625,stroke:#4facfe,stroke-width:2px,color:#ffffff;
    classDef specialistNode fill:#1a102f,stroke:#b8a2fc,stroke-width:1px,color:#ffffff;
    classDef itineraryNode fill:#281028,stroke:#f953c6,stroke-width:2px,color:#ffffff;
    classDef approvalNode fill:#2d1a0c,stroke:#f2994a,stroke-width:2px,color:#ffffff;
    classDef finalNode fill:#1e0c1e,stroke:#ff007f,stroke-width:2px,color:#ffffff;

    Start([User Input Query]) --> Guard{🛡️ Guardrail Node}
    class Start startEnd;
    class Guard guardNode;
    
    Guard -->|Invalid Query| Rejected[Show Rejection & Ask Again]
    class Rejected guardNode;
    
    Guard -->|Valid Request| Super[🤖 Supervisor Agent]
    class Super superNode;
    
    subgraph "Specialist Agent Layer (Parallel Execution)"
        Super -->|Selects| FA[✈️ Flight Agent]
        Super -->|Selects| HA[🏨 Hotel Agent]
        Super -->|Selects| WA[☀️ Weather Agent]
        Super -->|Selects| BA[💰 Budget Agent]
        
        class FA,HA,WA,BA specialistNode;
    end
    
    FA --> IT[📝 Itinerary Designer]
    HA --> IT
    WA --> IT
    BA --> IT
    class IT itineraryNode;
    
    IT --> Interrupt[🤝 Human-in-the-Loop Interrupt]
    class Interrupt approvalNode;
    
    Interrupt -->|User Requests Revisions| Super
    Interrupt -->|User Approves Itinerary| Concierge[🏆 Concierge / Final Response Agent]
    class Concierge finalNode;
    
    Concierge --> End([Render Timeline & Plan])
    class End startEnd;
```

---

## ✨ Features & Capabilities

### 🧠 Collaborative Agent Guild
*   **🛡️ Guardrail Agent**: Intercepts off-topic queries to prevent prompt injections and verify clean query parameters.
*   **🤖 Supervisor Agent**: Analyzes constraints (destination, budget, duration, preferences) and dynamically activates only the necessary specialists.
*   **✈️ Flight Agent**: Connects to the **AviationStack MCP** server to analyze airport registries, coordinate flight details, and locate regional airlines.
*   **🏨 Hotel Agent**: Queries the **Tavily MCP** client for live web-grounded comparisons, recommending three distinct options (Budget, Mid-range, Luxury) complete with neighborhood breakdowns and booking tips.
*   **☀️ Weather Agent**: Communicates with a custom-built local **Weather MCP** server to pull live conditions and multi-day forecasts, outputting packing tips.
*   **💰 Budget Agent**: Reviews airline, hotel, and general regional costs, conducting feasibility assessments and warning of financial risks.
*   **📝 Itinerary Agent**: Compiles the independent specialists' findings into a cohesive chronological plan.
*   **🏆 Concierge Agent**: Takes final inputs and formats a beautifully polished markdown document, free of LLM artifacts and raw system code.

### 🔄 Rate-Limit & Fallback Resilience
*   **TPM-Optimized Output Budgets**: Strict token-length caps are enforced (100–200 words max per specialist agent) to easily fit within Groq's low TPM constraints.
*   **Automatic Chain Fallbacks**: Configured with LangChain's `.with_fallbacks()` utility. If the primary model (`qwen3.6-27b` / custom Groq model) hits a rate or daily limit, the graph automatically and seamlessly routes transactions to backup models (`openai/gpt-oss-20b` followed by `openai/gpt-oss-120b`).

### 🎨 Elite User Experience (Streamlit Dark Theme)
*   **Pipeline Execution Trackbar**: Visual progress bar using high-fidelity emojis and CSS highlights that update in real-time as agents complete their tasks.
*   **Identified Constraints Metric Grid**: Clean, glassmorphic metric blocks dynamically summarizing destination, origin, budget, and travel preferences.
*   **Interactive Revision Portal**: An inline human-in-the-loop interface that prompts users for adjustments or approval after the draft is compiled.
*   **Chronological Day-by-Day Timeline**: Beautiful CSS vertical timeline cards replacing raw text layouts.
*   **Responsive Tables**: Overflow-scrolling CSS table containers (`.responsive-table-container`) styling hotel comparisons and flight registries so they fit perfectly on any device.
*   **Session Management Control Panel**: Sidebar controller displaying live session keys and allowing thread-switching.

---

## 📁 Project Structure

```text
├── agents.py                    # Specialist agent definitions, system prompts, and output parsing
├── config.py                    # API client configurations and LLM fallback chain logic
├── custom_weather_mcp_server.py # Custom fastmcp server communicating with OpenWeather API
├── frontend.py                  # Dark-themed Streamlit layout, custom styling, and timeline renderer
├── graph.py                     # LangGraph StateGraph orchestration and checkpointing setup
├── mcp_client.py                # MultiServerMCPClient connection manager linking Tavily, AviationStack, & Weather
├── state.py                     # TravelState state schema definitions
├── test_app.py                  # End-to-end programmatic CLI integration test script
├── travel_plans/                # Output directory where completed itineraries are saved to markdown
├── pyproject.toml               # Python project configuration
├── pyrefly.toml                 # Pyrefly packaging configuration
└── .env                         # API credentials and database connection string
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.10+ installed and the following API Keys:
*   **Groq API Key** (Primary model provider)
*   **Tavily API Key** (Hotel and accommodation search)
*   **OpenWeather API Key** (Weather forecasts)
*   **AviationStack API Key** (Airport and airline data)

### 2. Activate Virtual Environment & Install Packages
```bash
# Clone the repository and navigate inside
cd multi-agent-travel-planner

# Activate your virtual environment
source myenv/bin/activate  # On Linux/macOS
# or
myenv\Scripts\activate     # On Windows

# Install all required libraries
pip install streamlit langgraph langchain-core langchain-groq mcp requests python-dotenv psycopg psycopg-binary
```

### 3. Environment Configuration
Create a `.env` file in the root folder and add your credentials:
```env
GROQ_API_KEY=gsk_your_groq_api_key
TAVILY_API_KEY=tvly-your_tavily_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
AVIATION_STACK_API_KEY=your_aviationstack_api_key

# Optional: PostgreSQL Database connection string for stateful session persistence.
# If connection fails or is left blank, the app falls back to MemorySaver automatically.
DATABASE_URL=postgresql://username:password@localhost:5432/travel_planner
```

---

## 🏃 Running the Application

### Programmatic Integration Test
Validate the graph setup, model connection, and agent communication flow via the CLI:
```bash
python test_app.py
```

### Launch the Streamlit Frontend
Start the interactive travel planner client in your browser:
```bash
streamlit run frontend.py
```
Open your browser to `http://localhost:8501` to start planning your next journey!
