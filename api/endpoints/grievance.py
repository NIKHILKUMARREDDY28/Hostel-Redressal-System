from fastapi import APIRouter, Request

router = APIRouter()
from mongodb.greviance import get_all_active_grievances


@router.get("/")
async def ping_service(request: Request):
    return {"Message": "Responding from Greviance System"}


@router.get("/grievances")
async def get_all_grievances(request: Request):
    all_grievances = await get_all_active_grievances()

    return {"status": "success", "grievances": all_grievances}
