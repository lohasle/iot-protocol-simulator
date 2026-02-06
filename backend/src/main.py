"""
IoT Protocol Simulator - Main FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

# Add project root to path
sys.path.insert(0, '.')

from src.routers import devices, packets, protocols, simulation, metrics, alerts
from src.services.websocket_manager import ws_manager
from src.services.simulation_engine import simulation_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting IoT Protocol Simulator...")
    
    # Start simulation engine
    simulation_engine.start()
    
    # Start WebSocket manager
    await ws_manager.start()
    
    logger.info("IoT Protocol Simulator started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IoT Protocol Simulator...")
    simulation_engine.stop()
    await ws_manager.stop()
    logger.info("IoT Protocol Simulator stopped")


# Create FastAPI application
app = FastAPI(
    title="IoT Protocol Simulator API",
    description="World-class IoT protocol debugging platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devices.router, prefix="/api/v1")
app.include_router(packets.router, prefix="/api/v1")
app.include_router(protocols.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "IoT Protocol Simulator",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "simulation_running": simulation_engine.is_running}


@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time communication"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = await ws_manager.handle_message(websocket, data)
            if message:
                await websocket.send_text(message)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
