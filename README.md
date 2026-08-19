# ✈️ Real-World Multi-Agent AI Travel Planner

A state-of-the-art, autonomous multi-agent travel planning system built on **LangGraph**, powered by **Groq** (with automatic model fallbacks), and styled with a premium dark-themed **Streamlit** dashboard.

The application orchestrates a team of specialized agents—Guardrail, Supervisor, Flight, Hotel, Weather, Budget, Itinerary, and Concierge—collaborating to dynamically search real-time data, build a structured itinerary, and compile a polished, download-ready travel proposal.

---

## 🗺️ Architectural Workflow

The system is coordinated via a **StateGraph** in LangGraph. Conversation state is persisted using a PostgreSQL checkpointer (`PostgresSaver`) for active sessions and falls back automatically to in-memory tracking (`MemorySaver`) if the database is not configured.

```mermaid
flowchart TD
    Start([User Input Query]) --> Guard[🛡️ Guardrail Agent]
    Guard -->|Invalid| Rejected[Show Rejection / Ask Again]
    Guard -->|Valid| Super[🤖 Supervisor Agent]
    
    subgraph "Specialist Agents (Parallel Execution)"
        Super -->|Selects| FA[✈️ Flight Agent]
        Super -->|Selects| HA[🏨 Hotel Agent]
        Super -->|Selects| WA[☀️ Weather Agent]
        Super -->|Selects| BA[💰 Budget Agent]
    end
    
    FA --> IT[📝 Itinerary Agent]
    HA --> IT
    WA --> IT
    BA --> IT
    
    IT --> Interrupt{Approval Interrupt?}
    Interrupt -->|User Adjustments| Super
    Interrupt -->|Approved| Concierge[🏆 Concierge / Final Response Agent]
    
    Concierge --> End([Render Timeline & Plan])
```

---

## ✨ Features

- **🛡️ Input Guardrail & Validation**: Screens user queries to filter out off-topic requests and ensure clean, structured parameters.
- **🤖 Dynamic Supervisor Orchestration**: Analyzes queries and dynamically selects which specialist agents are required, avoiding unnecessary tool invocation.
- **⚙️ Multi-Agent Specialist Layer**:
  - **Flight Agent**: Provides carrier, routing, and booking guidance using live flight MCP data.
  - **Hotel Agent**: Selects budget, mid-range, and luxury accommodations using Tavily search.
  - **Weather Agent**: Details current temperature and forecast outlook via a custom Weather MCP server.
  - **Budget Agent**: Analyzes expenses, highlights price risks, and provides concrete saving tips.
- **🔄 Robust Token Rate-Limit Optimizations**:
  - Enforces tight output constraints (100–200 words per specialist agent) to guarantee compliance with the **8,000 TPM limit** of Groq's free models.
  - Implements **automatic LLM fallbacks** (`openai/gpt-oss-20b` and `openai/gpt-oss-120b`) in `config.py` using LangChain's `.with_fallbacks()` decorator, allowing 24/7 reliability even when primary Qwen daily token limits are exhausted.
- **🎨 Premium User Interface**: A bespoke, dark-themed Streamlit frontend featuring:
  - Responsive pipeline trackbars showing agent execution states.
  - Custom timeline renderers displaying daily activities.
  - Responsive, scroll-wrap HTML tables (`.responsive-table-container`) that adapt to any screen size without spilling over.
- **💾 Session Retention & Export**: Auto-saves travel plans to markdown and supports manual downloads.

---

## 📁 Project Structure

```text
├── agents.py                 # Core agent logic, system prompts, and text processing
├── config.py                 # LLM initialization (primary + fallback chains) and API credentials
├── custom_weather_mcp_server.py # Custom MCP server providing real-time weather information
├── frontend.py               # Streamlit application UI, timeline, and table rendering
├── graph.py                  # LangGraph StateGraph orchestration and compilation
├── mcp_client.py             # Client wrappers for connecting to Tavily, Weather, and Flight MCP tools
├── state.py                  # TravelState schemas and TypedDict models
├── test_app.py               # End-to-end programmatic testing script
├── travel_plans/             # Generated travel itineraries auto-save here
└── .env                      # API keys and Database connection URL
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Groq API Key (Free developer account available)
- Tavily API Key
- OpenWeather API Key
- AviationStack API Key

### 2. Setup Virtual Environment & Install Dependencies
Activate the local environment and install packages:

```bash
# Activate virtual environment
source myenv/bin/activate  # On Linux/macOS
# or
myenv\Scripts\activate     # On Windows

# Install required dependencies
pip install streamlit langgraph langchain-core langchain-groq tavily-python requests python-dotenv psycopg psycopg-binary
```

### 3. Environment Configuration
Create or modify the `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key

# Optional: PostgreSQL Database connection string for session retention.
# Falls back to MemorySaver (in-memory tracking) if database connection fails.
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

---

## 🏃 Running the Application

### Programmatic Integration Test
Run a dry test check of the entire supervisor and specialist pipeline using:

```bash
python test_app.py
```

### Start Streamlit Frontend
Launch the interactive agent planner dashboard:

```bash
streamlit run frontend.py
```

Open your browser to `http://localhost:8501` to start planning your next journey!
