# Backend - Fiber Route API

FastAPI backend with A* pathfinding algorithm and SSE streaming for real-time route computation visualization.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
.\venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST `/api/route`
Start a route computation task.

**Request Body:**
```json
{
  "from": "city_nyc",
  "to": "city_sf",
  "weights": [1.0, 0.5, 0.3]
}
```

**Response:**
```json
{
  "jobId": "uuid-here"
}
```

### GET `/api/route/stream?id={jobId}`
Stream real-time events from the A* algorithm via Server-Sent Events (SSE).

**Events:**
- `start`: Algorithm started
- `visit-node`: Node visited
- `relax-edge`: Edge relaxed
- `final-path`: Path found
- `fail`: No path found

## Project Structure

```
backend/
├── main.py                 # FastAPI app bootstrap
├── api/
│   ├── __init__.py
│   ├── route.py            # /api/route endpoints
│   └── stream.py           # SSE streaming endpoint
├── core/
│   ├── __init__.py
│   ├── graph.py            # Node, Edge, Graph classes
│   ├── search.py           # A* implementation with event hooks
│   └── weights.py          # Weighted cost function
├── services/
│   ├── __init__.py
│   ├── jobs.py             # Job manager for async search tasks
│   └── loader.py           # Loads graph.json into memory
└── data/
    └── graph.json          # Preprocessed graph data
```
