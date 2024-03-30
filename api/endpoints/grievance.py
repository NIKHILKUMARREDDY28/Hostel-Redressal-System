from fastapi import APIRouter,Request

router = APIRouter()


@router.get("/")
async def ping_service(request: Request):
    return {"Message": "Responding from Greviance System"}