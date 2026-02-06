# FastAPI Backend Placeholder
# IoT Protocol Simulator Backend

from fastapi import FastAPI

app = FastAPI(
    title="IoT Protocol Simulator API",
    description="Backend API for IoT Protocol Simulator",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "IoT Protocol Simulator API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Routes will be added in future iterations
