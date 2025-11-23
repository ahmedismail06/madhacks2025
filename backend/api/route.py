# ===========================================
# api/route.py — start route computation
# ===========================================

import threading
from flask import Blueprint, request, jsonify
from services.jobs import create_job, make_event_sender
from services.loader import load_graph
from core.dijkstra import dijkstra
from core.astar import astar
from core.weights import make_weight_function
import asyncio

route_bp = Blueprint('route', __name__)

# graph is loaded once at startup
graph = load_graph()


@route_bp.route("/route", methods=["POST"])
def start_route():
    # Get query parameters
    start = request.args.get('start')
    goal = request.args.get('goal')
    w_lat = request.args.get('w_lat')
    w_traffic = request.args.get('w_traffic')
    w_risk = request.args.get('w_risk')
    algorithm = request.args.get('algorithm', 'dijkstra')
    
    # Convert weight strings to floats
    w_lat_float = float(w_lat)
    w_traffic_float = float(w_traffic)
    w_risk_float = float(w_risk)
    
    print(f"[ROUTE API] Received request: {start} -> {goal}, weights=({w_lat_float}, {w_traffic_float}, {w_risk_float}), algo={algorithm}")

    job_id = create_job() # create new job
    send_event = make_event_sender(job_id) # event sender for this job
    weight_func = make_weight_function(w_lat_float, w_traffic_float, w_risk_float) # create weight function
    
    # Select search algorithm
    search_func = astar if algorithm == "a-star" else dijkstra
    
    # Run search algorithm in background thread
    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(search_func(graph, start, goal, weight_func, send_event))
        loop.close()
    
    thread = threading.Thread(target=run_async_task, daemon=True)
    thread.start()

    return jsonify({"jobId": job_id, "algorithm": algorithm})
