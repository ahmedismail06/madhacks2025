# ===========================================
# api/result.py - Get final pathfinding result
# ===========================================
# Returns simplified JSON result for most recent job.
# Polls until computation completes.

import time
from flask import Blueprint, jsonify
from services.jobs import get_result as get_job_result, get_last_job_id

result_bp = Blueprint('result', __name__)


@result_bp.route("/route/result", methods=["GET"])
def get_result():
    """
    Get final result from most recent pathfinding job.
    
    No parameters required - automatically uses last job.
    Polls until job completes (max 60 seconds).
    
    Returns:
        JSON with 'type' ('final-path' or 'no-path') and 'path' array
    """
    # Get the most recent job ID
    job_id = get_last_job_id()
    
    if job_id is None:
        response = jsonify({"error": "No route computation has been started"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    
    # Poll for result (max 60 seconds)
    max_wait = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        result = get_job_result(job_id)
        
        if result is None:
            response = jsonify({"error": "Job not found"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        if result["status"] == "completed":
            # Format response
            if result["path"] is not None:
                simplified_response = {
                    "type": "final-path",
                    "path": result["path"]  # Array of {x, y, type}
                }
            else:
                simplified_response = {
                    "type": "no-path",
                    "reason": "No route found"
                }
            
            response = jsonify(simplified_response)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Wait a bit before polling again
        time.sleep(0.1)
    
    # Timeout
    response = jsonify({"error": "Timeout waiting for route computation"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 408

