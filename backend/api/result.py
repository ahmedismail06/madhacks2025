# ===========================================
# api/result.py - Get final pathfinding result
# ===========================================
# Returns simplified JSON result for most recent job.
# Waits for computation to complete before responding.

import json
import asyncio
from flask import Blueprint, request, jsonify
from services.jobs import get_queue, get_last_job_id

result_bp = Blueprint('result', __name__)


@result_bp.route("/route/result", methods=["GET"])
def get_result():
    """
    Get final result from most recent pathfinding job.
    
    No parameters required - automatically uses last job.
    
    Returns:
        JSON with 'event' ('final-path' or 'no-path') and 'path' array
        or error if no job exists or timeout
    """
    # Get the most recent job ID
    job_id = get_last_job_id()
    
    if job_id is None:
        response = jsonify({"error": "No route computation has been started"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    
    queue = get_queue(job_id)
    
    if queue is None:
        response = jsonify({"error": "Job not found"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

    # Wait for final event from algorithm
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Poll queue until we find a final event
        final_event = None
        while True:
            event = loop.run_until_complete(asyncio.wait_for(queue.get(), timeout=60.0))
            
            # Check if batch event contains final result
            if event['event'] == 'batch':
                for e in event['data']:
                    if e['event'] in ['final-path', 'no-path']:
                        final_event = e
                        break
                if final_event:
                    break
            # Or direct final event
            elif event['event'] in ['final-path', 'no-path']:
                final_event = event
                break
        
        if final_event is None:
            raise Exception("No final event found")
        
        # Simplify response - only return path nodes
        if final_event['event'] == 'final-path':
            simplified_response = {
                "event": "final-path",
                "path": final_event['data']['path']  # Array of {x, y, type}
            }
        else:
            simplified_response = {
                "event": "no-path",
                "reason": final_event['data'].get('reason', 'No route found')
            }
        
        response = jsonify(simplified_response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except asyncio.TimeoutError:
        response = jsonify({"error": "Timeout waiting for route computation"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 408
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
    finally:
        loop.close()

