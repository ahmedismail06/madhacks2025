# ===========================================
# api/route.py — start route computation
# ===========================================

from fastapi import APIRouter, BackgroundTasks
from services.jobs import create_job, make_event_sender
from services.loader import load_graph
from core.search import dijkstra
from core.weights import make_weight_function

router = APIRouter()

# graph is loaded once at startup
graph = load_graph()


@router.post("/route")
async def start_route(body: dict, background: BackgroundTasks):
    # body contains: from, to, weights
    start = body["from"] # start node CITY NAME
    goal = body["to"] # goal node CITY NAME
    w_lat, w_traffic, w_risk = body["weights"]

    job_id = create_job() # create new job
    send_event = make_event_sender(job_id) # event sender for this job
    weight_func = make_weight_function(w_lat, w_traffic, w_risk) # create weight function
    # run Dijkstra in background
    background.add_task(
        dijkstra,
        graph,
        start,
        goal,
        weight_func,
        send_event
    )

    return {"jobId": job_id} # return job ID to client
