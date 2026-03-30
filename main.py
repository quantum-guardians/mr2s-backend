import uvicorn
from fastapi import FastAPI
from router import optimization_router, optimization_v1_router

app = FastAPI()

app.include_router(optimization_router)
app.include_router(optimization_v1_router)

@app.get("/")
async def root():
    return {"message": "Quantum Hackathon API"}

if '__main__' == __name__:
    uvicorn.run(app, host='0.0.0.0', port=8000)