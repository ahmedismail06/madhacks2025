# ===========================================
# api/stream.py — SSE streaming
# ===========================================

import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from services.jobs import get_queue

router = APIRouter()


@router.get("/route/stream")
async def stream_route(request: Request, id: str):
    print(f"[STREAM] Client connected to stream for job ID: {id}")
    print(f"[STREAM] Request headers: {dict(request.headers)}")
    print(f"[STREAM] Client host: {request.client.host if request.client else 'unknown'}")
    
    queue = get_queue(id) # get the queue for this job_id
    
    if queue is None:
        print(f"[STREAM ERROR] No queue found for job ID: {id}")
        return {"error": "Job not found"}

    async def event_generator():
        event_count = 0
        while True:
            if await request.is_disconnected():
                print(f"[STREAM] Client disconnected for job {id} after {event_count} events")
                break # client disconnected

            event = await queue.get() # wait for next event
            event_type = event['event'] # event type
            event_data = json.dumps(event['data']) # event data as JSON
            event_count += 1
            
            print(f"[STREAM] Sending event #{event_count} type={event_type} for job {id}")
            
            yield f"event: {event_type}\ndata: {event_data}\n\n" # yield event in SSE format

    return StreamingResponse(event_generator(), media_type="text/event-stream") # SSE streaming response    ) # SSE streaming response
