import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
AVIATION_STACK_API_KEY = os.getenv("AVIATION_STACK_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_llm():
    primary_model = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    primary_llm = ChatGroq(model=primary_model)
    
    # Fallback models in case primary model hits rate limit or daily limit
    fallbacks = [
        ChatGroq(model="openai/gpt-oss-20b"),
        ChatGroq(model="openai/gpt-oss-120b"),
    ]
    return primary_llm.with_fallbacks(fallbacks)
