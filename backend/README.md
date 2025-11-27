# NetworkNudge Backend - Fiber Optic Route Optimization API

A Flask-based REST API for finding optimal fiber optic network paths between cities using Dijkstra and A* pathfinding algorithms with real-time signal quality tracking.

## Overview

This backend service provides intelligent routing for fiber optic networks, considering multiple factors including:
- **Latency**: Physical distance and base transmission delays
- **Traffic Load**: Current network congestion levels
- **Risk Factors**: Security and reliability concerns for each fiber segment
- **Signal Quality**: Fiber optic attenuation with regeneration spot support

The API supports real-time algorithm visualization through Server-Sent Events (SSE), allowing frontends to display pathfinding progress as it happens.

## Architecture

```
backend/
├── main.py                 # Flask application entry point
├── requirements.txt        # Python dependencies
├── api/                    # REST API endpoints
│   ├── route.py           # POST /api/route - Start pathfinding job
│   ├── edges.py           # GET /api/route/edges - Get tried edges
│   └── result.py          # GET /api/route/result - Get final path JSON
├── core/                   # Pathfinding algorithms & data structures
│   ├── graph.py           # Node, Edge, Graph data structures
│   ├── weights.py         # Edge cost calculation functions
│   ├── dijkstra.py        # Dijkstra's algorithm implementation
│   └── astar.py           # A* algorithm implementation
├── services/              # Background job management & data loading
│   ├── jobs.py            # Job queue, result storage, job tracking
│   └── loader.py          # Load network graph from JSON files
└── data/                  # Network topology data
    ├── nodes.json         # Network nodes (cities, infrastructure, regen spots)
    ├── edges.json         # Fiber optic connections
    └── city_name_to_id.json  # City name to node ID mapping (generated)
```

## API Endpoints

### 1. Start Pathfinding Job
**POST** `/api/route`

Initiates a pathfinding computation in the background and returns immediately with a job ID.

**Query Parameters:**
- `start` (required): Starting city name (e.g., "New York")
- `goal` (required): Destination city name (e.g., "Los Angeles")
- `latency` (optional): Weight for latency factor (default: 1.0)
- `traffic` (optional): Weight for traffic load (default: 1.0)
- `risk` (optional): Weight for risk factor (default: 1.0)
- `algorithm` (optional): `"dijkstra"` or `"astar"` (default: "dijkstra")

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/route?start=New%20York&goal=Los%20Angeles&latency=1.5&traffic=1.0&risk=0.5&algorithm=astar"
```

**Response:**
```json
{
  "jobId": "abc123def456",
  "algorithm": "astar"
}
```

### 2. Get Explored Edges (JSON)
**GET** `/api/route/edges?id=<jobId>`

Returns all edges that were explored during the pathfinding algorithm.

**Query Parameters:**
- `id` (required): Job ID returned from POST /api/route

**Example Request:**
```bash
curl "http://localhost:8000/api/route/edges?id=abc123def456"
```

**Response (Running):**
```json
{
  "status": "running",
  "tried_edges": []
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "tried_edges": [
    {"start_x": 40.7128, "start_y": -74.0060, "end_x": 40.7580, "end_y": -73.9855},
    {"start_x": 40.7580, "start_y": -73.9855, "end_x": 41.8781, "end_y": -87.6298},
    ...
  ]
}
```

### 3. Get Final Result (JSON)
**GET** `/api/route/result`

Returns the final result of the most recently completed pathfinding job in simple JSON format.

**Example Request:**
```bash
curl "http://localhost:8000/api/route/result"
```

**Success Response:**
```json
{
  "type": "final-path",
  "path": [
    {"x": 40.7128, "y": -74.0060, "type": "city"},
    {"x": 40.7580, "y": -73.9855, "type": "network_node"},
    ...
  ]
}
```

**Failure Response:**
```json
{
  "type": "no-path",
  "reason": "No viable path found (signal quality degraded below 10%)"
}
```

## Algorithms

### Dijkstra's Algorithm
**Use When:** You want guaranteed shortest path or need to explore all possible routes uniformly.

- **Strategy**: Uniform-cost search - explores nodes in order of increasing total cost from start
- **Guarantee**: Always finds the optimal (lowest cost) path if one exists
- **Performance**: Explores more nodes than A*, but thorough and reliable
- **Best For**: Dense networks, when heuristic guidance isn't helpful, or when optimality is critical

### A* Algorithm
**Use When:** You want faster results and have a clear goal direction.

- **Strategy**: Heuristic-guided search - prioritizes nodes closer to goal using Euclidean distance
- **Guarantee**: Finds optimal path if heuristic is admissible (never overestimates)
- **Performance**: Typically faster than Dijkstra by focusing search toward goal
- **Best For**: Sparse networks, long-distance routes, when speed matters more than exhaustive exploration

Both algorithms track **signal quality** throughout the path and automatically reject routes that degrade below 10% signal strength.

## Signal Quality Model

Fiber optic cables experience signal attenuation over distance. This API models signal degradation using industry-standard decibel-based calculations:

**Attenuation Formula:**
```
total_attenuation_dB = (degrade_rate * distance) / 10
decay_factor = 10^(-total_attenuation_dB / 10)
new_signal_quality = current_signal_quality * decay_factor
```

**Key Parameters:**
- `degrade_rate`: Signal loss rate (dB/km) for each fiber segment (default: 0.025 dB/km)
- `distance`: Length of fiber cable in kilometers

**Regeneration Spots:**
- Special nodes of type `regen_spot` reset signal quality to 100%
- Allow long-distance paths that would otherwise fail due to signal loss
- Positioned strategically throughout the network

**Rejection Threshold:**
- Paths with signal quality below 10% are automatically rejected
- Forces pathfinding to route through regeneration spots on long routes

## Node Types

The network graph contains several types of nodes:

- **`city`**: Major cities (start/end points for routes)
- **`network_node`**: Intermediate routing infrastructure
- **`regen_spot`**: Signal regeneration stations (reset signal to 100%)
- **`routing`**: Routing junctions in the fiber network
- **`city_connection`**: Connection points between cities and network backbone

## Edge Properties

Each fiber optic connection has the following properties:

| Property | Description | Typical Range |
|----------|-------------|---------------|
| `distance` | Cable length in kilometers | 1-5000 km |
| `traffic_load` | Current congestion level | 0.0-1.0 |
| `base_ms` | Base latency per km | 0.001-0.01 ms/km |
| `risk` | Security/reliability risk score | 0.0-1.0 |
| `degrade_rate` | Signal attenuation rate (dB/km) | 0.01-0.05 dB/km |
| `geometry` | Array of [lat, lng] coordinates for path visualization | Optional |

## Weight Function

The cost of traversing an edge is calculated as a weighted sum:

```python
edge_cost = (latency_weight * latency_ms) + 
            (traffic_weight * traffic_load) + 
            (risk_weight * risk_score)

where:
  latency_ms = base_ms * distance
```

Users can adjust the three weights when calling the API to prioritize different factors:
- **High latency weight**: Prefer faster, shorter routes
- **High traffic weight**: Avoid congested network segments
- **High risk weight**: Route through more secure/reliable infrastructure

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**Key Dependencies:**
- Flask 3.0.0 - Web framework
- asyncio - Concurrent execution support

### Data Files
Ensure the following files exist in `data/` directory:
- `nodes.json` - Network node definitions
- `edges.json` - Fiber connection definitions

The `city_name_to_id.json` mapping file will be generated automatically on first run.

### Run Server
```bash
python main.py
```

Server will start on `http://localhost:8000` with the following configuration:
- **Host**: `0.0.0.0` (accessible from network)
- **Port**: `8000`
- **Debug mode**: Enabled (auto-reload on code changes)
- **Threading**: Enabled (handles concurrent requests)

### Health Check
Verify the server is running:
```bash
curl http://localhost:8000/
```

Expected response:
```json
{"message": "Fiber Route API", "status": "running"}
```

## Usage Example

Complete workflow for finding a route from New York to Los Angeles:

```bash
# 1. Start pathfinding job with A* algorithm
RESPONSE=$(curl -X POST "http://localhost:8000/api/route?start=New%20York&goal=Los%20Angeles&latency=1.5&traffic=1.0&risk=0.5&algorithm=astar")
JOB_ID=$(echo $RESPONSE | jq -r '.jobId')

# 2. Get all edges explored during pathfinding
curl "http://localhost:8000/api/route/edges?id=$JOB_ID"

# 3. Get final result as JSON
curl "http://localhost:8000/api/route/result"
```

## CORS Configuration

All endpoints include CORS headers to allow cross-origin requests from web frontends:
```
Access-Control-Allow-Origin: *
```

This enables the API to be consumed by single-page applications hosted on different domains.

## Performance Considerations

- **Concurrent Jobs**: Jobs run in background threads for non-blocking operation
- **Job Tracking**: Each job is tracked by unique ID, allowing multiple simultaneous pathfinding operations
- **Memory**: Graph data loaded once at startup and shared across all requests
- **Polling**: Result endpoint polls every 100ms until completion (max 60 seconds)
- **Scalability**: Consider using a production WSGI server (gunicorn, uwsgi) instead of Flask's development server

## Error Handling

The API includes comprehensive error handling:

- **Invalid city names**: Returns 400 Bad Request with error message
- **Missing parameters**: Returns 400 Bad Request listing required parameters
- **Pathfinding failures**: Returns `no-path` event with reason (signal degradation, no route exists, etc.)
- **Invalid job IDs**: Returns 404 Not Found or 500 error depending on context

## Future Enhancements

Potential improvements for production deployment:

- **Authentication**: Add API key or OAuth-based authentication
- **Rate Limiting**: Prevent abuse with request throttling
- **Database**: Store historical routes and job results
- **Caching**: Cache frequently requested routes
- **Monitoring**: Add logging, metrics, and alerting
- **Production Server**: Deploy with gunicorn/nginx instead of Flask dev server
- **WebSocket**: Upgrade from SSE to WebSocket for bidirectional communication

## License

[Add your license information here]

## Contributors

[Add contributor information here]
