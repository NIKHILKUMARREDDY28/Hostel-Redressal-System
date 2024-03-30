from fastapi import FastAPI, Request
import uvicorn
from api.api import api_router

app = FastAPI()

app.include_router(api_router, prefix="/api")


@app.get("/")
async def ping_service(request: Request):
    return {"Message": "Responding from Hostel System"}


if __name__ == "__main__":
    uvicorn.run(app)
