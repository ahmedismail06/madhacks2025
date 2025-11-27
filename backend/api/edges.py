# ===========================================
# api/edges.py - Edges retrieval endpoint
# ===========================================
# Returns all edges explored during pathfinding in JSON format.

import json
from flask import Blueprint, request, jsonify
from services.jobs import get_result

edges_bp = Blueprint('edges', __name__)


@edges_bp.route("/route/edges", methods=["GET"])
def get_edges():
    """
    Get all edges tried during pathfinding for a specific job.
    
    Query Parameters:
        id: Job ID returned from /route endpoint
    
    Returns:
        JSON with tried_edges array containing {start_x, start_y, end_x, end_y} objects
    """
    job_id = request.args.get('id')
    result = get_result(job_id)
    
    if result is None:
        return jsonify({"error": "Job not found"}), 404
    
    if result["status"] == "running":
        return jsonify({"status": "running", "tried_edges": []}), 202

    response = jsonify({
        "status": result["status"],
        "tried_edges": result["tried_edges"]
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
