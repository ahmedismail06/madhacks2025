# ===========================================
# api/result.py — get final result by job ID
# ===========================================

import json
import asyncio
from flask import Blueprint, request, jsonify
from services.jobs import get_queue, get_last_job_id

result_bp = Blueprint('result', __name__)


@result_bp.route("/route/result", methods=["GET"])
def get_result():
    # Get the last job ID
    job_id = get_last_job_id()
    
    if job_id is None:
        print(f"[RESULT ERROR] No jobs have been created yet")
        response = jsonify({"error": "No route computation has been started"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    
    print(f"[RESULT] Client requesting result for last job ID: {job_id}")
    
    queue = get_queue(job_id)
    
    if queue is None:
        print(f"[RESULT ERROR] No queue found for job ID: {job_id}")
        response = jsonify({"error": "Job not found"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

    # Wait for the final event
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Wait for events until we get a final one
        final_event = None
        while True:
            event = loop.run_until_complete(asyncio.wait_for(queue.get(), timeout=60.0))
            
            # Check if this is a batch event
            if event['event'] == 'batch':
                # Look for final-path or no-path in the batch
                for e in event['data']:
                    if e['event'] in ['final-path', 'no-path']:
                        final_event = e
                        break
                if final_event:
                    break
            elif event['event'] in ['final-path', 'no-path']:
                final_event = event
                break
        
        if final_event is None:
            raise Exception("No final event found")
        
        print(f"[RESULT] Received final event type={final_event['event']} for job {job_id}")
        
        # Simplify the response
        if final_event['event'] == 'final-path':
            simplified_response = {
                "event": "final-path",
                "path": final_event['data']['path']  # Already in {x, y, type} format
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
        print(f"[RESULT] Timeout for job {job_id}")
        response = jsonify({"error": "Timeout waiting for route computation"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 408
    except Exception as e:
        print(f"[RESULT ERROR] Exception for job {job_id}: {e}")
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
    finally:
        loop.close()

