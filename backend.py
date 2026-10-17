import json
import os
import uuid
import certifi
from dotenv import load_dotenv
from typing import TypedDict, Annotated
import operator

import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights


# ========================================================
# Environment
# ========================================================

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your Render PostgreSQL "
            "External Database URL to your .env file."
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Please add it to your .env file."
    )


# ========================================================
# Prompt / Context Limits
# ========================================================

MAX_FLIGHT_CHARS = 12_000
MAX_HOTEL_CHARS = 12_000
MAX_ITINERARY_CHARS = 18_000


def compact_for_prompt(value, max_chars: int) -> str:
    """
    Convert arbitrary tool output to text and cap its size before
    sending it to the LLM.
    """
    if value is None:
        return "No data available."

    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
                indent=2,
            )
        except Exception:
            text = str(value)

    text = text.strip()

    if not text:
        return "No data available."

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n[Additional results were truncated to fit the model context.]"
    )


def run_tavily_search(query: str):
    """
    Support either a normal Python callable or a LangChain tool
    exposing .invoke().
    """
    if hasattr(tavily_search, "invoke"):
        try:
            return tavily_search.invoke(query)
        except TypeError:
            return tavily_search.invoke({"query": query})

    return tavily_search(query)


# ========================================================
# LLM
# ========================================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.3,
    max_tokens=2500,
)


# ========================================================
# State
# ========================================================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int


# ========================================================
# Flight Agent
# ========================================================

def flight_agent(state: TravelState):
    query = state["user_query"].strip()
    flight_data = search_flights(query)

    return {
        "flight_results": compact_for_prompt(
            flight_data,
            MAX_FLIGHT_CHARS,
        )
    }


# ========================================================
# Hotel Agent
# ========================================================

def hotel_agent(state: TravelState):
    query = f"Best hotels for this travel request: {state['user_query']}"
    hotel_data = run_tavily_search(query)

    return {
        "hotel_results": compact_for_prompt(
            hotel_data,
            MAX_HOTEL_CHARS,
        )
    }


# ========================================================
# Itinerary Agent
# ========================================================

def itinerary_agent(state: TravelState):
    flight_results = compact_for_prompt(
        state.get("flight_results", ""),
        MAX_FLIGHT_CHARS,
    )
    hotel_results = compact_for_prompt(
        state.get("hotel_results", ""),
        MAX_HOTEL_CHARS,
    )

    print("USER QUERY CHARS:", len(state.get("user_query", "")))
    print("FLIGHT RESULTS CHARS:", len(flight_results))
    print("HOTEL RESULTS CHARS:", len(hotel_results))

    prompt = f"""
Create a complete travel itinerary based on the information below.

USER REQUEST:
{state['user_query']}

FLIGHT INFORMATION:
{flight_results}

HOTEL INFORMATION:
{hotel_results}

INSTRUCTIONS:
- Create a practical day-by-day itinerary.
- Be budget-aware.
- Use only the most useful flight and hotel information.
- Do not invent prices that are not present in the supplied data.
- If exact flight or hotel pricing is unavailable, clearly say so.
- Clearly label approximate budget figures as estimates.
- Keep the itinerary concise and easy to follow.
""".strip()

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are an expert travel planner. "
                    "Create concise, practical travel plans using only "
                    "the supplied information."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ========================================================
# Final Response Agent
# ========================================================

def final_agent(state: TravelState):
    flight_results = compact_for_prompt(
        state.get("flight_results", ""),
        6_000,
    )
    hotel_results = compact_for_prompt(
        state.get("hotel_results", ""),
        6_000,
    )
    itinerary = compact_for_prompt(
        state.get("itinerary", ""),
        MAX_ITINERARY_CHARS,
    )

    final_prompt = f"""
Generate the final travel response for the user.

USER REQUEST:
{state['user_query']}

KEY FLIGHT INFORMATION:
{flight_results}

KEY HOTEL INFORMATION:
{hotel_results}

TRAVEL ITINERARY:
{itinerary}

Format the final answer using these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Day-by-Day Itinerary
5. Estimated Budget
6. Final Recommendations

IMPORTANT:
- Be clear, concise, and practical.
- Do not invent flight prices.
- Do not invent hotel prices.
- If exact prices are unavailable, clearly state that they are unavailable.
- Label approximate budget figures as estimates.
- Mention that live/status flight APIs may not provide ticket prices.
- Avoid repeating the same flight or hotel information unnecessarily.
""".strip()

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a professional AI travel planning assistant. "
                    "Produce concise, accurate, practical travel recommendations."
                )
            ),
            HumanMessage(content=final_prompt),
        ]
    )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ========================================================
# Build Graph
# ========================================================

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# ========================================================
# PostgreSQL Checkpointer
# ========================================================

DATABASE_URL = get_database_url()

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    prepare_threshold=0,
    row_factory=dict_row,
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

travel_graph = graph.compile(checkpointer=checkpointer)


# ========================================================
# Function for FastAPI
# ========================================================

def run_travel_agent(
    user_input: str,
    thread_id: str | None = None,
):
    """
    Run the travel-planning workflow.

    Reusing the same thread_id allows LangGraph/PostgreSQL to associate
    subsequent requests with the same conversation checkpoint.
    """
    user_input = (user_input or "").strip()

    if not user_input:
        raise ValueError("user_input cannot be empty.")

    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        },
        config=config,
    )

    messages = result.get("messages", [])
    final_answer = (
        messages[-1].content
        if messages
        else "Unable to generate a travel response."
    )

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }
