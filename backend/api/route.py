# ===========================================
# api/route.py — start route computation
# ===========================================

from fastapi import APIRouter, BackgroundTasks, Response
from services.jobs import create_job, make_event_sender
from services.loader import load_graph
from core.dijkstra import dijkstra
from core.astar import astar
from core.weights import make_weight_function

router = APIRouter()

# graph is loaded once at startup
graph = load_graph()


@router.post("/route")
async def start_route(
    response: Response,
    background: BackgroundTasks,
    start: str,
    goal: str,
    w_lat: str,
    w_traffic: str,
    w_risk: str,
    algorithm: str
):
    # start and goal are CITY NAMES (URL decoded automatically by FastAPI)
    # Convert weight strings to floats
    w_lat_float = float(w_lat)
    w_traffic_float = float(w_traffic)
    w_risk_float = float(w_risk)
    
    print(f"[ROUTE API] Received request: {start} -> {goal}, weights=({w_lat_float}, {w_traffic_float}, {w_risk_float}), algo={algorithm}")
    
    # Set CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

    job_id = create_job() # create new job
    send_event = make_event_sender(job_id) # event sender for this job
    weight_func = make_weight_function(w_lat_float, w_traffic_float, w_risk_float) # create weight function
    
    # Select search algorithm
    search_func = astar if algorithm == "a-star" else dijkstra
    
    # run search algorithm in background
    background.add_task(
        search_func,
        graph,
        start,
        goal,
        weight_func,
        send_event
    )

    return {"jobId": job_id, "algorithm": algorithm} # return job ID and algorithm to client
