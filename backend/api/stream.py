# ===========================================
# api/stream.py — SSE streaming
# ===========================================

import json
import asyncio
from flask import Blueprint, request, Response
from services.jobs import get_queue

stream_bp = Blueprint('stream', __name__)


@stream_bp.route("/route/stream", methods=["GET"])
def stream_route():
    job_id = request.args.get('id')
    
    print(f"[STREAM] Client connected to stream for job ID: {job_id}")
    print(f"[STREAM] Request headers: {dict(request.headers)}")
    print(f"[STREAM] Client host: {request.remote_addr}")
    
    queue = get_queue(job_id) # get the queue for this job_id
    
    if queue is None:
        print(f"[STREAM ERROR] No queue found for job ID: {job_id}")
        return json.dumps({"error": "Job not found"}), 404

    def event_generator():
        event_count = 0
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while True:
                # Get event from queue
                event = loop.run_until_complete(asyncio.wait_for(queue.get(), timeout=30.0))
                event_type = event['event']
                event_data = json.dumps(event['data'])
                event_count += 1
                
                print(f"[STREAM] Sending event #{event_count} type={event_type} for job {job_id}")
                
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                
        except asyncio.TimeoutError:
            print(f"[STREAM] Timeout for job {job_id} after {event_count} events")
        except Exception as e:
            print(f"[STREAM ERROR] Exception for job {job_id}: {e}")
        finally:
            loop.close()
            print(f"[STREAM] Stream closed for job {job_id} after {event_count} events")

    return Response(event_generator(), mimetype="text/event-stream")
