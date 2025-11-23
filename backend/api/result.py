# ===========================================
# api/result.py — get final result by job ID
# ===========================================

import json
import asyncio
from flask import Blueprint, request, jsonify
from services.jobs import get_queue

result_bp = Blueprint('result', __name__)


@result_bp.route("/route/result", methods=["GET"])
def get_result():
    job_id = request.args.get('id')
    
    print(f"[RESULT] Client requesting result for job ID: {job_id}")
    
    queue = get_queue(job_id)
    
    if queue is None:
        print(f"[RESULT ERROR] No queue found for job ID: {job_id}")
        response = jsonify({"error": "Job not found"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

    # Wait for the final event (since we're only sending final-path or no-path now)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Wait for the single final event
        event = loop.run_until_complete(asyncio.wait_for(queue.get(), timeout=60.0))
        print(f"[RESULT] Received final event type={event['event']} for job {job_id}")
        
        response = jsonify(event)
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
