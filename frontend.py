import uuid
import re
import json
import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app

# Set premium page layout
st.set_page_config(
    page_title="Real-World Multi-Agent Travel Planner", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Style Injection (Vanilla CSS)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Global Styles */
.stApp {
    background-color: #0b0f19;
    font-family: 'Inter', sans-serif;
    color: #cbd5e0;
}

h1, h2, h3, .main-title {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Custom Card Style */
.agent-card {
    background: rgba(17, 22, 37, 0.75);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: all 0.3s ease;
}

.agent-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 242, 254, 0.3);
    box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.1);
}

.card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Specific Card Accents */
.card-flight { border-top: 4px solid #00f2fe; }
.card-hotel { border-top: 4px solid #b8a2fc; }
.card-weather { border-top: 4px solid #f2994a; }
.card-budget { border-top: 4px solid #38ef7d; }
.card-itinerary { border-top: 4px solid #f953c6; }
.card-final { border-top: 4px solid #ff007f; background: rgba(26, 17, 37, 0.8); }

/* Badges */
.agent-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    background: rgba(255,255,255,0.08);
    color: #cbd5e0;
    border: 1px solid rgba(255,255,255,0.1);
}

.badge-flight { color: #00f2fe; border-color: rgba(0, 242, 254, 0.3); background: rgba(0, 242, 254, 0.05); }
.badge-hotel { color: #b8a2fc; border-color: rgba(184, 162, 252, 0.3); background: rgba(184, 162, 252, 0.05); }
.badge-weather { color: #f2994a; border-color: rgba(242, 153, 74, 0.3); background: rgba(242, 153, 74, 0.05); }
.badge-budget { color: #38ef7d; border-color: rgba(56, 239, 125, 0.3); background: rgba(56, 239, 125, 0.05); }
.badge-itinerary { color: #f953c6; border-color: rgba(249, 83, 198, 0.3); background: rgba(249, 83, 198, 0.05); }
.badge-final { color: #ff007f; border-color: rgba(255, 0, 127, 0.3); background: rgba(255, 0, 127, 0.05); }

/* Pipeline Execution Flow styles */
.pipeline-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 24px 0;
    padding: 20px;
    background: rgba(17, 22, 37, 0.4);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}
.pipeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
    transition: all 0.3s ease;
}
.pipeline-step.pending {
    opacity: 0.35;
}
.pipeline-step.not-selected {
    opacity: 0.15;
}
.pipeline-step.active {
    opacity: 1;
    transform: scale(1.05);
}
.pipeline-step.completed {
    opacity: 1;
}
.step-icon {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: #1b1e2c;
    border: 2px solid #33384a;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}
.pipeline-step.active .step-icon {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
    border-color: #00f2fe;
    box-shadow: 0 0 15px rgba(0, 242, 254, 0.5);
}
.pipeline-step.completed .step-icon {
    background: linear-gradient(135deg, #11998e, #38ef7d);
    border-color: #38ef7d;
    box-shadow: 0 0 10px rgba(56, 239, 125, 0.3);
}
.step-name {
    font-size: 0.75rem;
    font-weight: 500;
    color: #a0aec0;
    text-align: center;
}
.pipeline-step.active .step-name {
    color: #00f2fe;
    font-weight: 600;
}
.pipeline-step.completed .step-name {
    color: #38ef7d;
}
.pipeline-line {
    flex-grow: 1;
    height: 2px;
    background: rgba(255, 255, 255, 0.1);
    margin: 0 8px;
    margin-bottom: 24px;
    border-radius: 1px;
}
.pipeline-line.completed {
    background: linear-gradient(90deg, #38ef7d, #00f2fe);
}

/* Timeline/Itinerary Styling */
.timeline-container {
    position: relative;
    padding-left: 30px;
    margin: 20px 0;
}
.timeline-container::before {
    content: '';
    position: absolute;
    left: 9px;
    top: 5px;
    bottom: 5px;
    width: 2px;
    background: linear-gradient(to bottom, #f953c6, #9d50bb);
}
.timeline-item {
    position: relative;
    margin-bottom: 30px;
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: -30px;
    top: 4px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #0b0f19;
    border: 4px solid #f953c6;
    box-shadow: 0 0 10px rgba(249, 83, 198, 0.4);
}
.timeline-day {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    color: #f953c6;
    font-size: 1.15rem;
    margin-bottom: 8px;
}
.timeline-content {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 12px;
    padding: 16px;
}

/* Interactive Approval Alert Box */
.approval-container {
    background: rgba(242, 153, 74, 0.05);
    border: 1px solid rgba(242, 153, 74, 0.2);
    border-left: 5px solid #f2994a;
    border-radius: 12px;
    padding: 20px;
    margin: 24px 0;
    box-shadow: 0 4px 20px rgba(242, 153, 74, 0.08);
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #070a13 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Streamlit button overrides */
div.stButton > button {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
    color: #070a13 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 14px 0 rgba(0, 242, 254, 0.3) !important;
    transition: all 0.3s ease !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(0, 242, 254, 0.5) !important;
    color: #ffffff !important;
}

div.stDownloadButton > button {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #cbd5e0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
}

div.stDownloadButton > button:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    color: #ffffff !important;
}

.metric-grid {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.metric-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 12px 18px;
    min-width: 120px;
    flex-grow: 1;
}

.metric-label {
    font-size: 0.75rem;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.metric-value {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# ----------------- Helper Functions for HTML Rendering -----------------

def md_to_html(md_text: str) -> str:
    if not md_text:
        return ""
    
    html = md_text
    
    # Escape simple HTML tags
    html = html.replace("<", "&lt;").replace(">", "&gt;")
    # Re-allow thinks
    html = html.replace("&lt;think&gt;", "<think>").replace("&lt;/think&gt;", "</think>")
    
    # Headers
    html = re.sub(r'^### (.*?)$', r'<h4 style="color:#ffffff; margin-top:12px; margin-bottom:8px; font-family:\'Outfit\'; font-weight:600; font-size:1.05rem;">\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h3 style="color:#ffffff; margin-top:16px; margin-bottom:12px; font-family:\'Outfit\'; font-weight:600; font-size:1.2rem;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h2 style="color:#ffffff; margin-top:20px; margin-bottom:16px; font-family:\'Outfit\'; font-weight:700; font-size:1.4rem;">\1</h2>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Bullet points
    html = re.sub(r'^\s*-\s+(.*?)$', r'<li style="margin-bottom:6px; color:#cbd5e0; line-height:1.6; font-size:0.92rem;">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^\s*\*\s+(.*?)$', r'<li style="margin-bottom:6px; color:#cbd5e0; line-height:1.6; font-size:0.92rem;">\1</li>', html, flags=re.MULTILINE)
    
    lines = html.split('\n')
    processed_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            continue
            
        if stripped.startswith('<li'):
            if not in_list:
                processed_lines.append('<ul style="padding-left:20px; margin-bottom:12px; margin-top:6px;">')
                in_list = True
            processed_lines.append(line)
        else:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            if stripped.startswith('<h') or stripped.startswith('<div') or stripped.startswith('</div') or stripped.startswith('<table') or stripped.startswith('</table') or stripped.startswith('<tr') or stripped.startswith('<td') or stripped.startswith('<th'):
                processed_lines.append(line)
            else:
                processed_lines.append(f'<p style="margin-bottom:12px; color:#cbd5e0; line-height:1.6; font-size:0.92rem;">{line}</p>')
                
    if in_list:
        processed_lines.append('</ul>')
        
    return '\n'.join(processed_lines)

def parse_markdown_tables(html_text: str) -> str:
    lines = html_text.split('\n')
    table_started = False
    table_html = []
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Strip any paragraph wrapping that md_to_html might have added
        p_match = re.match(r'^<p[^>]*>(\|.*\|)</p>$', stripped)
        if p_match:
            stripped = p_match.group(1).strip()
            
        # Simple table identification
        if stripped.startswith('|') and stripped.endswith('|'):
            if not table_started:
                table_started = True
                table_html = ['<table style="width:100%; border-collapse:collapse; margin:16px 0; border: 1px solid rgba(255,255,255,0.08); border-radius:8px; overflow:hidden;">']
                
            cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
            
            # Skip divider line (e.g. |---|---|)
            if all(cell.replace('-', '').replace(':', '') == '' for cell in cells):
                continue
                
            row_html = '<tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">'
            for cell in cells:
                # Replace strong indicators inside tables
                cleaned_cell = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cell)
                if len(table_html) == 1:
                    row_html += f'<th style="background: rgba(255,255,255,0.04); padding: 10px 14px; text-align: left; font-weight: 600; color: #ffffff; font-size: 0.85rem; border-bottom: 2px solid rgba(255,255,255,0.1);">{cleaned_cell}</th>'
                else:
                    row_html += f'<td style="padding: 10px 14px; color: #cbd5e0; font-size: 0.82rem; line-height: 1.4;">{cleaned_cell}</td>'
            row_html += '</tr>'
            table_html.append(row_html)
        else:
            if table_started:
                table_html.append('</table>')
                new_lines.append('\n'.join(table_html))
                table_started = False
            new_lines.append(line)
            
    if table_started:
        table_html.append('</table>')
        new_lines.append('\n'.join(table_html))
        
    return '\n'.join(new_lines)

def format_itinerary_as_timeline(text: str) -> str:
    if not text:
        return ""
        
    lines = text.split('\n')
    html = '<div class="timeline-container">'
    
    current_day_header = None
    current_day_lines = []
    
    def render_current_day():
        if not current_day_header:
            return ""
        content_text = "\n".join(current_day_lines).strip()
        formatted_content = md_to_html(content_text)
        formatted_content = parse_markdown_tables(formatted_content)
        
        return f"""
        <div class="timeline-item">
            <div class="timeline-day">{current_day_header}</div>
            <div class="timeline-content">
                {formatted_content}
            </div>
        </div>
        """

    intro_lines = []
    has_started_days = False
    
    for line in lines:
        stripped = line.strip()
        # Match "Day X:" or similar patterns, with optional markdown headers/bolds
        day_match = re.match(r'^(?:###\s+|\*\*)?(Day\s+\d+[:\-]?.*?)(?:\*\*)?$', stripped, re.IGNORECASE)
        
        if day_match:
            has_started_days = True
            if current_day_header:
                html += render_current_day()
            current_day_header = day_match.group(1).strip()
            current_day_lines = []
        else:
            if has_started_days:
                current_day_lines.append(line)
            else:
                intro_lines.append(line)
                
    if current_day_header:
        html += render_current_day()
        
    html += '</div>'
    
    if not has_started_days:
        return md_to_html(text)
        
    intro_html = md_to_html("\n".join(intro_lines).strip()) if intro_lines else ""
    return intro_html + html


def render_agent_card(title, icon, content, category):
    html_content = md_to_html(content)
    html_content = parse_markdown_tables(html_content)
    
    card_html = f"""
    <div class="agent-card card-{category}">
        <div class="card-title">
            <span style="font-size: 1.4rem;">{icon}</span>
            <span style="color: #ffffff; font-family: 'Outfit'; font-weight: 600; font-size:1.15rem;">{title}</span>
            <span class="agent-badge badge-{category}" style="margin-left: auto;">{category.upper()}</span>
        </div>
        <div class="card-content">
            {html_content}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_pipeline(selected_agents, current_state_results, waiting_for_approval):
    all_steps = [
        {"id": "supervisor", "name": "Supervisor", "icon": "🤖"},
        {"id": "flight_agent", "name": "Flights", "icon": "✈️"},
        {"id": "hotel_agent", "name": "Hotels", "icon": "🏨"},
        {"id": "weather_agent", "name": "Weather", "icon": "☀️"},
        {"id": "budget_agent", "name": "Budget", "icon": "💰"},
        {"id": "itinerary_agent", "name": "Itinerary", "icon": "📝"},
        {"id": "approval", "name": "Approval", "icon": "🤝"},
        {"id": "final_response", "name": "Final Plan", "icon": "🏆"}
    ]
    
    html = '<div class="pipeline-container">'
    
    for i, step in enumerate(all_steps):
        status = 'pending'
        
        if step["id"] == "supervisor":
            status = "completed"
        elif step["id"] == "approval":
            if current_state_results.get("final_response"):
                status = "completed"
            elif waiting_for_approval:
                status = "active"
            elif current_state_results.get("itinerary"):
                status = "completed"
        elif step["id"] == "final_response":
            if current_state_results.get("final_response"):
                status = "completed"
        else:
            is_selected = step["id"] in selected_agents
            result_key = f"{step['id'].replace('_agent', '')}_results"
            has_result = bool(current_state_results.get(result_key))
            
            if not is_selected:
                status = "not-selected"
            elif has_result:
                status = "completed"
            else:
                status = "active"
                
        step_class = f"pipeline-step {status}"
        
        html += f"""
        <div class="{step_class}">
            <div class="step-icon">{step['icon']}</div>
            <div class="step-name">{step['name']}</div>
        </div>
        """
        
        if i < len(all_steps) - 1:
            line_status = 'completed' if status == 'completed' else 'pending'
            html += f'<div class="pipeline-line {line_status}"></div>'
            
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ----------------- Streamlit UI Application Logic -----------------

# Render the high-tech generated banner
st.image("header.png", use_container_width=True)

# Main Title Section
st.markdown('<h1 class="main-title" style="margin-top: 20px; margin-bottom: 5px;">Multi-Agent Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #a0aec0; margin-bottom: 25px; font-size: 1.05rem;">An autonomous AI team crafting hyper-personalized, budget-optimized travel itineraries.</p>', unsafe_allow_html=True)

# Initialize Session State
with st.sidebar:
    st.markdown('<h3 style="color:#ffffff; font-family:\'Outfit\'; margin-bottom: 15px;">Control Panel</h3>', unsafe_allow_html=True)
    user_id = st.text_input("User ID", value="demo_user")
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        
    if st.button("Start New Planning Thread", use_container_width=True):
        st.session_state.thread_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        st.session_state.pop("waiting_for_approval", None)
        st.session_state.pop("latest_result", None)
        st.rerun()
        
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 12px; margin-top: 15px;">
        <span style="font-size:0.75rem; color:#718096; text-transform:uppercase;">Active Session ID</span><br/>
        <code style="color:#00f2fe; font-size:0.85rem;">{st.session_state.thread_id}</code>
    </div>
    """, unsafe_allow_html=True)

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Travel query input
query = st.text_area(
    "Where would you like to travel?",
    placeholder="Plan a 7-day Japan trip under Rs. 2 lakh. I prefer budget hotels and no overnight flights.",
    height=120,
)

if st.button("Launch AI Travel Agents", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a travel request first.")
    else:
        with st.spinner("Supervisor is assigning tasks to Flight, Hotel, Weather, and Budget agents..."):
            result = app.invoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "user_id": user_id,
                    "user_query": query,
                    "flight_results": "",
                    "hotel_results": "",
                    "weather_results": "",
                    "budget_results": "",
                    "itinerary": "",
                    "final_response": "",
                    "llm_calls": 0,
                },
                config=config,
            )
        st.session_state.latest_result = result
        st.session_state.waiting_for_approval = "__interrupt__" in result
        st.rerun()

# Check for results
result = st.session_state.get("latest_result")

if result:
    selected_agents = result.get("selected_agents", [])
    
    # Render Execution Flow
    st.divider()
    st.markdown('<h2 style="color:#ffffff; font-family:\'Outfit\';">Agent Execution Pipeline</h2>', unsafe_allow_html=True)
    render_pipeline(selected_agents, result, st.session_state.get("waiting_for_approval", False))
    
    # Display Constraints
    constraints = result.get("trip_constraints", {})
    if constraints:
        st.markdown('<h3 style="color:#ffffff; font-family:\'Outfit\'; margin-bottom: 12px;">Identified Constraints</h3>', unsafe_allow_html=True)
        
        pref_str = ", ".join(constraints.get("special_preferences", [])) or "None"
        
        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-item">
                <div class="metric-label">📍 Destination</div>
                <div class="metric-value">{constraints.get('destination', 'N/A') or 'N/A'}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">🛫 Origin</div>
                <div class="metric-value">{constraints.get('origin', 'N/A') or 'Anywhere'}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">⏱️ Duration</div>
                <div class="metric-value">{constraints.get('duration', 'N/A') or 'N/A'}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">💰 Budget</div>
                <div class="metric-value">{constraints.get('budget', 'N/A') or 'N/A'}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">🎒 Style</div>
                <div class="metric-value">{constraints.get('travel_style', 'N/A') or 'Standard'}</div>
            </div>
            <div class="metric-item" style="min-width: 200px;">
                <div class="metric-label">⭐ Preferences</div>
                <div class="metric-value" style="font-size:0.95rem;">{pref_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Supervisor Reasoning Card
    st.markdown('<h3 style="color:#ffffff; font-family:\'Outfit\'; margin-top: 25px;">Supervisor Decision</h3>', unsafe_allow_html=True)
    st.info(result.get("supervisor_reasoning", "Routing request to designated agents."))

    # Specialist Columns
    reports = []
    if result.get("flight_results"):
        reports.append(("Flight Intelligence Report", "✈️", result["flight_results"], "flight"))
    if result.get("weather_results"):
        reports.append(("Weather Forecast & Climate Analysis", "☀️", result["weather_results"], "weather"))
    if result.get("hotel_results"):
        reports.append(("Accommodation Recommendations", "🏨", result["hotel_results"], "hotel"))
    if result.get("budget_results"):
        reports.append(("Budget Feasibility Assessment", "💰", result["budget_results"], "budget"))

    if reports:
        st.markdown('<h2 style="color:#ffffff; font-family:\'Outfit\'; margin-top:35px;">Specialist Agents Intelligence Reports</h2>', unsafe_allow_html=True)
        if len(reports) == 1:
            title, icon, content, category = reports[0]
            render_agent_card(title, icon, content, category)
        else:
            col1, col2 = st.columns(2)
            for idx, (title, icon, content, category) in enumerate(reports):
                if idx % 2 == 0:
                    with col1:
                        render_agent_card(title, icon, content, category)
                else:
                    with col2:
                        render_agent_card(title, icon, content, category)

    # Draft Itinerary Section
    st.markdown('<h2 style="color:#ffffff; font-family:\'Outfit\'; margin-top:35px;">Draft Itinerary Proposal</h2>', unsafe_allow_html=True)
    
    if "__interrupt__" in result:
        draft = result["__interrupt__"][0].value.get("draft_itinerary", "")
    else:
        draft = result.get("itinerary", "")
        
    if draft:
        timeline_html = format_itinerary_as_timeline(draft)
        st.markdown(f"""
        <div class="agent-card card-itinerary">
            <div class="card-title">
                <span style="font-size: 1.4rem;">📝</span>
                <span style="color: #ffffff; font-family: 'Outfit'; font-weight: 600; font-size:1.15rem;">Itinerary Draft</span>
                <span class="agent-badge badge-itinerary" style="margin-left: auto;">ITINERARY</span>
            </div>
            <div class="card-content" style="margin-top: 15px;">
                {timeline_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Human Approval Node Interrupt
if st.session_state.get("waiting_for_approval") and result:
    st.markdown('<h2 style="color:#ffffff; font-family:\'Outfit\'; margin-top:35px;">🤝 Collaborative Planning: Human Review</h2>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="approval-container">
        <h4 style="color:#f2994a; margin-top:0; font-family:'Outfit'; font-weight:600; font-size:1.1rem; margin-bottom:8px;">Action Required: Review Draft Proposal</h4>
        <p style="color:#e2e8f0; font-size:0.92rem; line-height:1.5; margin:0;">
            The itinerary agent has created a draft proposal based on flights, hotels, weather, and budget constraints. 
            Please review it above and choose whether to proceed with polishing this plan or request adjustments.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    approved = st.radio("Do you approve this draft?", ["Yes, it looks great!", "No, I need some adjustments"], horizontal=True)
    feedback = st.text_area("Adjustment Requests / Feedback", disabled=approved == "Yes, it looks great!", placeholder="Describe what you want to change (e.g. 'swap Day 2 and Day 3', 'suggest more budget-friendly hotel options', 'add a free walking tour')...", height=100)
    
    if st.button("Submit Decision", type="primary", use_container_width=True):
        with st.spinner("Updating plan with feedback..."):
            final_result = app.invoke(
                Command(
                    resume={
                        "approved": approved == "Yes, it looks great!",
                        "feedback": feedback,
                    }
                ),
                config=config,
            )
        st.session_state.latest_result = final_result
        st.session_state.waiting_for_approval = False
        st.rerun()

# Final Travel Plan Display
final_result = st.session_state.get("latest_result")
if final_result and final_result.get("final_response"):
    st.divider()
    st.markdown('<h2 style="color:#ffffff; font-family:\'Outfit\'; margin-top:35px;">🏆 Final Polished Travel Plan</h2>', unsafe_allow_html=True)
    
    render_agent_card(
        "Polished Travel Itinerary & Advice", 
        "🏆", 
        final_result["final_response"], 
        "final"
    )
    
    # Export Capabilities
    export_content = f"""# Travel Plan: {final_result.get('user_query')}
    
## Supervisor Agent Orchestration Plan
{final_result.get('supervisor_reasoning')}

---

"""
    if final_result.get("flight_results"):
        export_content += f"## Flight Guidance\n{final_result['flight_results']}\n\n---\n\n"
    if final_result.get("hotel_results"):
        export_content += f"## Hotel Guidance\n{final_result['hotel_results']}\n\n---\n\n"
    if final_result.get("weather_results"):
        export_content += f"## Weather Guidance\n{final_result['weather_results']}\n\n---\n\n"
    if final_result.get("budget_results"):
        export_content += f"## Budget Assessment\n{final_result['budget_results']}\n\n---\n\n"
        
    export_content += f"## Detailed Itinerary\n{final_result.get('itinerary', '')}\n\n---\n\n"
    export_content += f"## Final Polished Travel Plan\n{final_result['final_response']}"
    
    st.download_button(
        label="📥 Download Full Travel Plan (Markdown)",
        data=export_content,
        file_name=f"travel_plan_{user_id}_{st.session_state.thread_id}.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    # Follow-up adjustments chat input
    st.divider()
    st.markdown('<h3 style="color:#ffffff; font-family:\'Outfit\';">💬 Request Revisions or Extensions</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:#cbd5e0; font-size:0.92rem; margin-bottom: 12px;">You can continue the chat and adjust this plan. For example, try asking: <i>"Can you swap out the budget hotels for 4-star options?"</i> or <i>"Add 2 more days to the itinerary."</i></p>', unsafe_allow_html=True)
    
    follow_up = st.text_input("Revision Request", key="follow_up_input", placeholder="Enter your follow-up adjustments here...")
    
    if st.button("Apply Adjustments", type="primary", use_container_width=True):
        if follow_up.strip():
            with st.spinner("Applying adjustments..."):
                result = app.invoke(
                    {
                        "messages": [HumanMessage(content=follow_up)],
                        "user_id": user_id,
                        "user_query": follow_up,
                    },
                    config=config,
                )
                st.session_state.latest_result = result
                st.session_state.waiting_for_approval = "__interrupt__" in result
                st.session_state.follow_up_input = ""  # Clear the input box!
                st.rerun()