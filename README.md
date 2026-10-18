# TripMate AI — A Multi-Agent Travel Planner with LangGraph

TripMate AI is an AI-powered travel planning application built with **LangGraph**, **FastAPI**, **Groq**, and external travel/search APIs.

The application uses a multi-step agent workflow to gather flight information, research hotels, generate a day-by-day itinerary, and create a final travel plan based on the user's request.

The project also includes a responsive web interface built with **HTML, CSS, and JavaScript**.

---

## Features

- Multi-agent travel planning workflow
- Natural-language travel requests
- Flight lookup using AviationStack
- Hotel research using Tavily Search
- AI-generated day-by-day travel itineraries
- Estimated budget recommendations
- Persistent conversation threads using PostgreSQL
- LangGraph checkpointing
- Groq-powered LLM responses
- Responsive FastAPI frontend
- Markdown-rendered AI responses
- Expandable flight, hotel, and itinerary details
- Copy itinerary
- Print itinerary
- Download itinerary
- API health monitoring
- Persistent browser session using `thread_id`
- Mobile-responsive UI

---

## Tech Stack

### Backend

- Python 3.11
- FastAPI
- Uvicorn
- LangGraph
- LangChain
- Pydantic

### AI

- Groq
- Llama / supported Groq chat models
- LangChain message interfaces

### External APIs

- AviationStack
- Tavily Search

### Database

- PostgreSQL
- Psycopg
- LangGraph `PostgresSaver`

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2
- Marked.js
- DOMPurify

---

## Multi-Agent Architecture

TripMate AI processes each travel request through a LangGraph workflow.

```text
                    User Request
                         │
                         ▼
                  ┌──────────────┐
                  │ Flight Agent │
                  └──────┬───────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ Hotel Agent │
                  └──────┬──────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Itinerary Agent │
                └────────┬────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ Final Agent │
                  └──────┬──────┘
                         │
                         ▼
                   Final Response
```

### Flight Agent

The Flight Agent processes the user's travel request and retrieves relevant flight information using the AviationStack API.

It supports natural-language requests such as:

```text
Plan a 7 day trip to Japan from Dallas.
```

and resolves locations into airport IATA codes before querying the flight API.

---

### Hotel Agent

The Hotel Agent uses Tavily Search to research hotel options based on the travel request.

The results are passed into the itinerary-planning workflow as additional context.

---

### Itinerary Agent

The Itinerary Agent combines:

- User travel requirements
- Flight information
- Hotel research

and sends the information to the Groq LLM to create a practical day-by-day itinerary.

Large tool responses are trimmed before being passed to the LLM to help prevent context-window errors.

---

### Final Response Agent

The Final Agent combines the itinerary and the most relevant travel information into a polished response containing:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Day-by-Day Itinerary
5. Estimated Budget
6. Final Recommendations

The model is instructed not to invent exact flight or hotel prices when pricing information is unavailable.

---

## Project Structure

```text
TripMate-AI/
│
├── app.py
├── backend.py
├── requirements.txt
├── .env
│
├── tools/
│   ├── flight_tool.py
│   └── tavily_tool.py
│
├── templates/
│   └── index.html
│
└── static/
    ├── styles.css
    └── app.js
```

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd TripMate-AI---A-Multi-Agent-Travel-Planner-with-LangGraph
```

---

### 2. Create the Conda environment

Create and activate the Conda environment:

```bash
conda create -n travel python=3.11 -y
conda activate travel
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key

DATABASE_URL=your_postgresql_database_url

DEFAULT_ORIGIN_IATA=DFW
```

`DEFAULT_ORIGIN_IATA` is optional and is used when a destination is detected but the user does not explicitly provide an origin.

For example:

```text
Plan a 7 day Japan trip.
```

could use:

```text
DFW
```

as the default origin.

Do not commit your `.env` file to GitHub.

Add the following to `.gitignore`:

```text
.env
__pycache__/
*.pyc
```

---

## Running the Application

Start the FastAPI application:

```bash
python app.py
```

The application runs locally at:

```text
http://127.0.0.1:8000
```

You can also access the interactive FastAPI API documentation at:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Home

```http
GET /
```

Loads the TripMate AI frontend.

---

### Travel Planner

```http
POST /api/travel
```

Processes a travel request through the LangGraph workflow.

Example request:

```json
{
  "message": "Plan a 7 day trip to Japan from Dallas with a moderate budget.",
  "thread_id": null
}
```

Example response structure:

```json
{
  "success": true,
  "thread_id": "user_example_thread",
  "answer": "Generated travel plan...",
  "flight_results": "Flight information...",
  "hotel_results": "Hotel research...",
  "itinerary": "Generated itinerary...",
  "llm_calls": 2
}
```

The returned `thread_id` can be sent with later requests to continue the same LangGraph conversation.

---

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "message": "AI Travel Planner API is running"
}
```

---

## Conversation Persistence

TripMate AI uses LangGraph's PostgreSQL checkpointer.

Each conversation is associated with a:

```text
thread_id
```

The frontend stores the current thread ID in browser `localStorage`.

This allows subsequent requests to reuse the same LangGraph conversation checkpoint.

The backend uses:

```python
PostgresSaver
```

with PostgreSQL for persistent graph state.

---

## Flight Search

The flight tool converts natural-language locations into IATA airport codes.

Examples:

```text
Dallas → DFW
London → LHR
Tokyo → HND
Japan → HND
Bangladesh → DAC
```

Example request:

```text
Plan a 7 day Japan trip from Bangladesh.
```

can be resolved approximately as:

```text
DAC → HND
```

The flight integration is primarily intended for live or status-related flight information.

Exact airfare pricing may not be available through the flight API.

---

## Context Management

External search APIs can return large amounts of text.

Passing all raw results directly into an LLM can exceed the model's context window.

TripMate AI therefore limits the amount of flight, hotel, and itinerary data passed between LLM nodes.

Example:

```python
MAX_FLIGHT_CHARS = 12000
MAX_HOTEL_CHARS = 12000
MAX_ITINERARY_CHARS = 18000
```

This helps prevent errors such as:

```text
Please reduce the length of the messages or completion.
```

---

## Frontend

The TripMate AI frontend provides a chat-style travel planning experience.

Features include:

- Responsive dark UI
- Quick travel prompts
- Chat-style user and AI messages
- Loading indicators for agent workflow stages
- API health indicator
- Persistent conversation session
- Markdown formatting
- Expandable agent results

The frontend communicates with FastAPI using:

```javascript
fetch("/api/travel")
```

---

## Itinerary Actions

Generated itineraries can be reused outside the application.

### Copy

The **Copy Itinerary** button copies the generated itinerary to the system clipboard.

A fallback method is included for environments where the modern browser Clipboard API is unavailable.

### Print

The **Print Itinerary** button opens a clean print-friendly version of the itinerary.

The navigation, chat UI, and other application elements are excluded from the printed version.

### Download

The **Download Itinerary** button saves the generated itinerary as a Markdown file.

Example:

```text
Tokyo-7-Day-Trip-itinerary.md
```

---

## Example Prompts

```text
Plan a 7 day trip to Japan from Dallas with a moderate budget.
```

```text
Plan a 5 day London trip from Dallas including flights, hotels, attractions, and a budget.
```

```text
Plan a budget-friendly 6 day trip to Mexico City from Dallas.
```

```text
Plan a 10 day trip to Italy from Dallas visiting Rome, Florence, and Venice.
```

---

## Security

API keys and database credentials should always be stored as environment variables.

Do not commit values such as:

```text
GROQ_API_KEY
TAVILY_API_KEY
AVIATIONSTACK_API_KEY
DATABASE_URL
```

to source control.

---

## Limitations

TripMate AI is designed as a travel-planning assistant and portfolio project.

Some limitations include:

- Flight APIs may not provide airfare pricing.
- Hotel search results may not contain real-time room availability.
- AI-generated budgets should be treated as estimates.
- Prices and schedules can change.
- Users should verify flight, hotel, and attraction information before booking.

---

## Future Improvements

Potential future enhancements include:

- Real-time flight pricing API integration
- Real-time hotel booking APIs
- Weather integration
- Maps and destination visualization
- Attraction and restaurant agents
- User authentication
- Saved trips
- Conversation history UI
- PDF itinerary downloads
- Email itinerary sharing
- Currency conversion
- Travel-date extraction
- Parallel LangGraph agent execution
- Dynamic agent routing based on user intent
- Custom trip budget tracking

---

## Disclaimer

TripMate AI provides travel-planning assistance and estimated recommendations.

Flight prices, hotel prices, schedules, availability, and travel requirements should always be verified with the appropriate provider before making a reservation or purchase.

---

## Author

Built as a hands-on AI engineering project demonstrating:

- LangGraph workflows
- Multi-agent application design
- LLM integration
- FastAPI development
- REST APIs
- PostgreSQL persistence
- External API integration
- Prompt/context management
- JavaScript frontend development
- AI-powered travel planning