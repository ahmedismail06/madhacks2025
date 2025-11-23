# ===========================================
# main.py — FastAPI bootstrap
# ===========================================

from fastapi import FastAPI
#from fastapi.middleware import add_middleware 
from fastapi.middleware.cors import CORSMiddleware
from api.route import router as route_router
from api.stream import router as stream_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],  # In production, replace with specific origins
    allow_credentials=True,  # Changed to True
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers
)

app.include_router(route_router, prefix="/api")
app.include_router(stream_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Fiber Route API", "status": "running"}
