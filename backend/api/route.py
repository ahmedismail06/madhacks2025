# ===========================================
# api/route.py - Route computation endpoint
# ===========================================
# Initiates pathfinding computation in background thread.
# Returns job ID for tracking progress.

import threading
from flask import Blueprint, request, jsonify
from services.jobs import create_job, store_result
from services.loader import load_graph
from core.dijkstra import dijkstra
from core.astar import astar
from core.weights import make_weight_function

route_bp = Blueprint('route', __name__)

# Load network graph once at startup
graph = load_graph()


@route_bp.route("/route", methods=["POST"])
def start_route():
    """
    Start pathfinding computation between two cities.
    
    Query Parameters:
        start: Starting city name
        goal: Destination city name
        w_lat: Weight for latency factor (float)
        w_traffic: Weight for traffic factor (float)
        w_risk: Weight for risk factor (float)
        algorithm: 'dijkstra' or 'a-star' (default: 'dijkstra')
    
    Returns:
        JSON with jobId and algorithm name
    """
    # Extract query parameters
    start = request.args.get('start')
    goal = request.args.get('goal')
    w_lat = request.args.get('w_lat')
    w_traffic = request.args.get('w_traffic')
    w_risk = request.args.get('w_risk')
    algorithm = request.args.get('algorithm', 'dijkstra')
    
    # Convert weights to floats
    w_lat_float = float(w_lat)
    w_traffic_float = float(w_traffic)
    w_risk_float = float(w_risk)

    # Create job
    job_id = create_job()
    weight_func = make_weight_function(w_lat_float, w_traffic_float, w_risk_float)
    
    # Select algorithm (A* or Dijkstra)
    search_func = astar if algorithm == "a-star" else dijkstra
    
    # Run pathfinding in background thread to avoid blocking
    def run_task():
        path, tried_edges = search_func(graph, start, goal, weight_func)
        store_result(job_id, path, tried_edges)
    
    thread = threading.Thread(target=run_task, daemon=True)
    thread.start()

    # Return job ID immediately
    response = jsonify({"jobId": job_id, "algorithm": algorithm})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
