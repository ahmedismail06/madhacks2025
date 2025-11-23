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
    queue = get_queue(id) # get the queue for this job_id

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break # client disconnected

            event = await queue.get() # wait for next event
            event_type = event['event'] # event type
            event_data = json.dumps(event['data']) # event data as JSON
            
            yield f"event: {event_type}\ndata: {event_data}\n\n" # yield event in SSE format

    return StreamingResponse(event_generator(), media_type="text/event-stream") # SSE streaming response
