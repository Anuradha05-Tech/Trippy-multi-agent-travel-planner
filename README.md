# ✈️ Multi-Agent AI Travel Booking System

A state-of-the-art, multi-agent travel planning system built on **LangGraph**, powered by **Groq (LLaMA 3.3 70B)**, and styled with a premium dark-themed **Streamlit** frontend. 

The application orchestrates specialized agents—Flight, Hotel, Itinerary, and Final—working sequentially to search real-time data, build a structured itinerary, and compile a comprehensive travel proposal.

---

## 🗺️ Architectural Workflow

The system is powered by **LangGraph** to coordinate agents via a sequential graph workflow. State is persisted using a PostgreSQL checkpointer (`PostgresSaver`) for active sessions and falls back gracefully to in-memory tracking (`MemorySaver`) if a database connection is not established.

```mermaid
graph TD
    START([Start Query]) --> FA[✈️ Flight Agent]
    FA --> HA[🏨 Hotel Agent]
    HA --> IA[🗓️ Itinerary Agent]
    IA --> FI[🧠 Final Agent]
    FI --> END([End / Render Plan])

    subgraph State Retention & APIs
        FA -.->|AviationStack API| FA_API[(Flight DB)]
        HA -.->|Tavily Search API| HA_API[(Web Search)]
        IA -.->|Groq LLaMA 3.3| LLM_IA[LLM Core]
        FI -.->|Groq LLaMA 3.3| LLM_FI[LLM Core]
        State[(PostgreSQL / Memory checkpointer)] -.-> FA
        State -.-> HA
        State -.-> IA
        State -.-> FI
    end
```

---

## ✨ Features

- **Sequential Multi-Agent Pipeline**: Specialized agents handle different parts of the travel search and itinerary planning.
- **Real-Time Data Integration**:
  - **AviationStack API** gathers live flight records based on query matching.
  - **Tavily Search API** retrieves up-to-date hotel details and sightseeing information.
- **Session-Based State Persistence**: Keeps track of conversation history and agents' state per thread using PostgreSQL checkpointer persistence.
- **Premium User Interface**: Modern, custom-styled Streamlit interface featuring a sleek dark mode layout, progress trackbars, interactive metrics, and destination cards.
- **Export & Auto-Save**: Auto-saves travel plans as markdown files inside the `travel_plans/` folder and allows manual downloads via a download button.

---

## 🛠️ Tech Stack

- **Framework**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **Large Language Model**: [Groq Cloud (LLaMA 3.3 70B Versatile)](https://groq.com/)
- **Frontend UI**: [Streamlit](https://streamlit.io/)
- **Search Engine**: [Tavily AI Search](https://tavily.com/)
- **Flight API**: [AviationStack API](https://aviationstack.com/)
- **Database / Checkpointer**: [PostgreSQL (via psycopg)](https://www.postgresql.org/)

---

## 📁 Project Structure

```text
├── tools/
│   ├── flight_tool.py      # Connects to AviationStack API for flight availability
│   └── tavily_tool.py      # Queries Tavily search engine for hotels/activities
├── travel_plans/           # Generated markdown plans are auto-saved here
├── main.py                 # Core LangGraph workflow definition, nodes, and checkpointer setup
├── frontend.py             # Sleek Streamlit dark-mode application UI
├── .env                    # Environment API keys and database configuration
├── pyproject.toml          # Project metadata & Pyrefly tool configurations
└── pyrefly.toml            # Python environment definitions
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- A Groq API Key, Tavily API Key, and AviationStack API Key.

### 2. Install Dependencies
Activate the local virtual environment and install the required packages:

```bash
# Activate virtual environment
source myenv/bin/activate  # Or your platform-specific activation command

# Install dependencies
pip install streamlit langgraph langchain-core langchain-groq tavily-python requests python-dotenv psycopg psycopg-binary
```

### 3. Environment Configuration
Create or modify the `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
TAVILY_API_KEY=your_tavily_api_key

# Optional: PostgreSQL Database connection string for session retention.
# If omitted, the graph automatically falls back to in-memory tracking.
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

---

## 🏃 Running the Application

### Backend Workflow Test
You can run a dry test run of the agent pipeline directly in your terminal:

```bash
python main.py
```

### Run Streamlit Web Application
To launch the full visual agent dashboard, run:

```bash
streamlit run frontend.py
```

Open `http://localhost:8501` in your browser to start planning!
