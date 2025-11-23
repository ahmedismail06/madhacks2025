# ===========================================
# api/route.py — start route computation
# ===========================================

from fastapi import APIRouter, BackgroundTasks
from services.jobs import create_job, make_event_sender
from services.loader import load_graph
from core.dijkstra import dijkstra
from core.astar import astar
from core.weights import make_weight_function

router = APIRouter()

# graph is loaded once at startup
graph = load_graph()


@router.post("/route")
async def start_route(body: dict, background: BackgroundTasks):
    # body contains: from, to, weights, algorithm (optional)
    start = body["from"] # start node CITY NAME
    goal = body["to"] # goal node CITY NAME
    w_lat, w_traffic, w_risk = body["weights"]
    algorithm = body.get("algorithm", "dijkstra")  # default to dijkstra

    job_id = create_job() # create new job
    send_event = make_event_sender(job_id) # event sender for this job
    weight_func = make_weight_function(w_lat, w_traffic, w_risk) # create weight function
    
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
